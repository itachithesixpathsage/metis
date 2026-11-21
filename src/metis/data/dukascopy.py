"""Dukascopy historical candle adapter using the dukascopy-node CLI."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import shlex
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from metis.core.config import get_settings
from metis.data.provider import HistoricalProvider
from metis.data.schemas import OHLCObservation

logger = logging.getLogger(__name__)

_TRADING_TIMEZONE = ZoneInfo("Europe/Riga")
_TIMEFRAME_SECONDS = {"M1": 60, "M15": 15 * 60, "H1": 60 * 60}


@dataclass(frozen=True)
class CommandResult:
    payload: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


class DukascopyAcquisitionError(RuntimeError):
    """A Dukascopy request failed or did not satisfy its trading grid."""

    retryable = False


class DukascopyIncompleteDataError(DukascopyAcquisitionError):
    """A response remained incomplete after all configured request retries."""


class DukascopyProvider(HistoricalProvider):
    name = "dukascopy"
    instruments = {"EURUSD": "eurusd", "GBPUSD": "gbpusd", "USDJPY": "usdjpy"}
    timeframes = {"M1": "m1", "M15": "m15", "H1": "h1"}

    def __init__(self, executable: str | None = None, cache_directory: str | Path | None = None,
                 batch_size: int | None = None, batch_pause_ms: int | None = None,
                 retries: int | None = None, runner: Any = None):
        settings = get_settings().market_data
        self.executable = shlex.split(executable or settings.dukascopy_executable)
        if not self.executable:
            raise ValueError("Dukascopy executable command must not be empty")
        self.cache_directory = Path(cache_directory or settings.dukascopy_cache_directory)
        self.batch_size = batch_size or settings.dukascopy_batch_size
        self.batch_pause_ms = batch_pause_ms if batch_pause_ms is not None else settings.dukascopy_batch_pause_ms
        self.retries = settings.dukascopy_retries if retries is None else retries
        if self.retries < 0:
            raise ValueError("retries must be zero or greater")
        self._runner = runner or self._run

    async def _run(self, args: list[str]) -> CommandResult:
        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        output_path = Path(args[args.index("-dir") + 1]) / f"{args[args.index('-fn') + 1]}.json"
        payload = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        return CommandResult(payload=payload, stdout=stdout.decode(errors="replace"),
                             stderr=stderr.decode(errors="replace"),
                             returncode=process.returncode if process.returncode is not None else -1)

    @staticmethod
    def _coerce_result(result: Any) -> CommandResult:
        if isinstance(result, CommandResult):
            return result
        if isinstance(result, str):
            # Preserve compatibility with existing injected runners.
            return CommandResult(payload=result)
        raise TypeError("Dukascopy runner must return text or CommandResult")

    @staticmethod
    def _parse_json(payload: str) -> list[dict[str, Any]]:
        text = payload.strip()
        if not text:
            return []
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            start = min((i for i in (text.find("["), text.find("{")) if i >= 0), default=-1)
            if start < 0:
                raise ValueError("dukascopy-node returned no JSON candle data") from None
            result = json.loads(text[start:])
        if isinstance(result, dict):
            result = result.get("data", result.get("candles", [result]))
        if not isinstance(result, list) or not all(isinstance(row, dict) for row in result):
            raise ValueError("dukascopy-node JSON must contain a list of candle objects")
        return result

    @staticmethod
    def expected_timestamps(start: datetime, end: datetime, timeframe: str) -> list[datetime]:
        """Return expected bars in the Dukascopy FX session, clipped to [start, end).

        The supported FX instruments trade from Monday 00:00 through Saturday
        00:00 Europe/Riga time. This corresponds to the broker's 22:00 UTC
        winter / 21:00 UTC summer Sunday open and Friday close. Iterating in UTC
        handles DST transitions without inventing local wall-clock minutes.
        """
        step = _TIMEFRAME_SECONDS[timeframe]
        start_utc = start.astimezone(UTC)
        end_utc = end.astimezone(UTC)
        first_epoch = ((int(start_utc.timestamp()) + step - 1) // step) * step
        cursor = datetime.fromtimestamp(first_epoch, UTC)
        expected: list[datetime] = []
        while cursor < end_utc:
            if cursor.astimezone(_TRADING_TIMEZONE).weekday() < 5:
                expected.append(cursor)
            cursor += timedelta(seconds=step)
        return expected

    @staticmethod
    def _timestamp(row: dict[str, Any]) -> datetime:
        return datetime.fromtimestamp(float(row["timestamp"]) / 1000, UTC)

    @staticmethod
    def _version(result: CommandResult) -> str:
        match = re.search(r"dukascopy-node:cli:version\s+([^\s]+)",
                          f"{result.stdout}\n{result.stderr}")
        return match.group(1) if match else "unknown"

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    async def _request_daily(self, *, symbol: str, timeframe: str, side: str,
                             day_start: datetime, day_end: datetime, expected: list[datetime],
                             requested_start: datetime, requested_end: datetime,
                             range_expected_count: int, run_dir: Path
                             ) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
        """Fetch a daily artifact with retry, validation, and preserved attempts."""
        instrument = self.instruments[symbol]
        timeframe_code = self.timeframes[timeframe]
        expected_set = set(expected)
        previous_timestamps: set[datetime] | None = None
        previous_rows: dict[datetime, dict[str, Any]] | None = None
        version = "unknown"
        attempt_artifacts: list[dict[str, Any]] = []
        last_validation: dict[str, Any] = {}
        accepted_rows: list[dict[str, Any]] = []

        for attempt in range(self.retries + 1):
            stem = (f"{day_start:%Y%m%d}-{symbol}-{timeframe}-{side}-attempt-{attempt + 1}")
            output_dir = run_dir / "cli-output"
            output_dir.mkdir(parents=True, exist_ok=True)
            args = [*self.executable, "-i", instrument,
                "-from", day_start.isoformat(timespec="seconds"),
                "-to", day_end.isoformat(timespec="seconds"),
                "-t", timeframe_code, "-p", side, "-utc", "0",
                "-f", "json", "-v", "-vu", get_settings().market_data.dukascopy_volume_units,
                "-fl",
                "-dir", str(output_dir), "-fn", stem,
                "--retries", "0", "--retry-on-empty",
                "--batch-size", str(self.batch_size), "--batch-pause", str(self.batch_pause_ms),
                "--debug"]
            outcome = "failed"
            result = CommandResult(payload="")
            attempt_validation: dict[str, Any] = {
                "downloaded_observation_count": 0,
                "expected_observation_count": len(expected),
                "missing_timestamps": [stamp.isoformat() for stamp in expected],
                "duplicate_timestamps": [],
                "unexpected_timestamps": [],
                "out_of_order_pairs": [],
            }
            raw_path = output_dir / f"{stem}.json"
            log_path = output_dir / f"{stem}.log"
            attempt_manifest_path = output_dir / f"{stem}.provenance.json"
            try:
                result = self._coerce_result(await self._runner(args))
                detected_version = self._version(result)
                if detected_version != "unknown":
                    version = detected_version
                raw_path.write_text(result.payload, encoding="utf-8")
                log_path.write_text(f"{result.stdout}\n{result.stderr}", encoding="utf-8")
                if result.returncode:
                    raise RuntimeError(f"dukascopy-node exited with status {result.returncode}")
                rows = self._parse_json(result.payload)
                scoped: list[tuple[datetime, dict[str, Any]]] = []
                duplicate_stamps: set[datetime] = set()
                ordered_stamps: list[datetime] = []
                seen: set[datetime] = set()
                unexpected_stamps: set[datetime] = set()
                for row in rows:
                    stamp = self._timestamp(row)
                    if not (day_start <= stamp < day_end):
                        continue
                    ordered_stamps.append(stamp)
                    if stamp in seen:
                        duplicate_stamps.add(stamp)
                    seen.add(stamp)
                    if stamp not in expected_set:
                        unexpected_stamps.add(stamp)
                        continue
                    scoped.append((stamp, row))

                present = {stamp for stamp, _ in scoped}
                missing = sorted(expected_set - present)
                out_of_order = [
                    {"previous": before.isoformat(), "current": after.isoformat()}
                    for before, after in zip(ordered_stamps, ordered_stamps[1:], strict=False)
                    if after < before
                ]
                last_validation = {
                    "downloaded_observation_count": len(scoped),
                    "expected_observation_count": len(expected),
                    "missing_timestamps": [stamp.isoformat() for stamp in missing],
                    "duplicate_timestamps": [stamp.isoformat() for stamp in sorted(duplicate_stamps)],
                    "unexpected_timestamps": [stamp.isoformat() for stamp in sorted(unexpected_stamps)],
                    "out_of_order_pairs": out_of_order,
                }
                attempt_validation = last_validation
                current_timestamps = set(ordered_stamps)
                comparison = None
                if previous_timestamps is not None:
                    current_rows = dict(scoped)
                    comparison = {
                        "previous_observation_count": len(previous_timestamps),
                        "retry_observation_count": len(current_timestamps),
                        "added_timestamps": [stamp.isoformat() for stamp in sorted(current_timestamps - previous_timestamps)],
                        "removed_timestamps": [stamp.isoformat() for stamp in sorted(previous_timestamps - current_timestamps)],
                        "changed_observations": [stamp.isoformat() for stamp in sorted(
                            current_timestamps & previous_timestamps
                        ) if previous_rows and current_rows.get(stamp) != previous_rows.get(stamp)],
                    }
                previous_timestamps = current_timestamps
                previous_rows = dict(scoped)
                attempt_artifacts.append({
                    "attempt": attempt + 1,
                    "raw_artifact_location": str(raw_path),
                    "sha256": self._sha256(raw_path),
                    "log_location": str(log_path),
                    "outcome": "incomplete" if (
                        missing or duplicate_stamps or unexpected_stamps or out_of_order
                    ) else "complete",
                    "validation": last_validation,
                    "comparison_with_previous": comparison,
                })

                if not missing and not duplicate_stamps and not unexpected_stamps and not out_of_order:
                    accepted_rows = [row for _, row in scoped]
                    outcome = "complete"
                else:
                    outcome = "incomplete"
                    if attempt < self.retries:
                        logger.warning("Dukascopy daily response incomplete; retrying",
                            extra={"symbol": symbol, "timeframe": timeframe, "price_side": side,
                                   "day": day_start.date().isoformat(), "attempt": attempt + 1,
                                   "retry": attempt + 1, "missing_count": len(missing),
                                   "duplicate_count": len(duplicate_stamps),
                                   "unexpected_count": len(unexpected_stamps),
                                   "out_of_order_count": len(out_of_order),
                                   "retry_outcome": "scheduled"})
            except Exception as exc:
                if not raw_path.exists():
                    raw_path.write_text(result.payload, encoding="utf-8")
                if not log_path.exists():
                    log_path.write_text(
                        f"{result.stdout}\n{result.stderr}\n{type(exc).__name__}: {exc}\n",
                        encoding="utf-8")
                attempt_artifacts.append({
                    "attempt": attempt + 1,
                    "raw_artifact_location": str(raw_path),
                    "sha256": self._sha256(raw_path),
                    "log_location": str(log_path),
                    "outcome": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "validation": attempt_validation,
                })
                outcome = "failed"
                attempt_manifest_path.write_text(json.dumps({
                    "provider": self.name,
                    "cli_version": version,
                    "instrument": instrument,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "price_side": side,
                    "requested_start_utc": requested_start.isoformat(),
                    "requested_end_utc_exclusive": requested_end.isoformat(),
                    "range_expected_observation_count_per_side": range_expected_count,
                    "daily_request_start_utc": day_start.isoformat(),
                    "daily_request_end_utc_exclusive": day_end.isoformat(),
                    "expected_observation_count": len(expected),
                    "downloaded_observation_count": attempt_validation["downloaded_observation_count"],
                    "request_count": len(attempt_artifacts),
                    "retry_count": len(attempt_artifacts) - 1,
                    "missing_timestamps": attempt_validation["missing_timestamps"],
                    "final_validation_status": "failed",
                    "raw_artifacts": attempt_artifacts,
                }, indent=2), encoding="utf-8")
                if attempt == self.retries:
                    logger.error("Dukascopy request retries exhausted",
                        extra={"symbol": symbol, "timeframe": timeframe, "price_side": side,
                               "day": day_start.date().isoformat(), "attempt": attempt + 1,
                               "retry_outcome": "aborted", "error": str(exc)})
                    raise DukascopyAcquisitionError(
                        f"Dukascopy request failed for {symbol} {timeframe} {side} "
                        f"on {day_start.date()}: {exc}; ingestion aborted for review") from exc
                logger.warning("Dukascopy request failed; retrying",
                    extra={"symbol": symbol, "timeframe": timeframe, "price_side": side,
                           "day": day_start.date().isoformat(), "attempt": attempt + 1,
                           "retry": attempt + 1, "retry_outcome": "scheduled", "error": str(exc)})

            logger.info("Dukascopy daily request attempt finished",
                extra={"symbol": symbol, "timeframe": timeframe, "price_side": side,
                       "day": day_start.date().isoformat(), "attempt": attempt + 1,
                       "retry_outcome": outcome,
                       "downloaded_count": attempt_validation.get("downloaded_observation_count", 0),
                       "expected_count": len(expected)})
            attempt_manifest_path.write_text(json.dumps({
                "provider": self.name,
                "cli_version": version,
                "instrument": instrument,
                "symbol": symbol,
                "timeframe": timeframe,
                "price_side": side,
                "requested_start_utc": requested_start.isoformat(),
                "requested_end_utc_exclusive": requested_end.isoformat(),
                "range_expected_observation_count_per_side": range_expected_count,
                "daily_request_start_utc": day_start.isoformat(),
                "daily_request_end_utc_exclusive": day_end.isoformat(),
                "expected_observation_count": len(expected),
                "downloaded_observation_count": attempt_validation.get(
                    "downloaded_observation_count", 0),
                "request_count": len(attempt_artifacts),
                "retry_count": len(attempt_artifacts) - 1,
                "missing_timestamps": attempt_validation.get("missing_timestamps", []),
                "duplicate_timestamps": attempt_validation.get("duplicate_timestamps", []),
                "unexpected_timestamps": attempt_validation.get("unexpected_timestamps", []),
                "out_of_order_pairs": attempt_validation.get("out_of_order_pairs", []),
                "final_validation_status": outcome,
                "raw_artifacts": attempt_artifacts,
            }, indent=2), encoding="utf-8")
            if outcome == "complete":
                summary = {
                    "request_count": len(attempt_artifacts),
                    "retry_count": len(attempt_artifacts) - 1,
                    "attempts": attempt_artifacts,
                    "validation": last_validation,
                }
                return accepted_rows, summary, version
            if attempt == self.retries:
                logger.error("Dukascopy incompleteness persisted after retries",
                    extra={"symbol": symbol, "timeframe": timeframe, "price_side": side,
                           "day": day_start.date().isoformat(), "attempt": attempt + 1,
                           "missing_count": len(attempt_validation.get("missing_timestamps", [])),
                           "duplicate_count": len(attempt_validation.get("duplicate_timestamps", [])),
                           "unexpected_count": len(attempt_validation.get("unexpected_timestamps", [])),
                           "out_of_order_count": len(attempt_validation.get("out_of_order_pairs", [])),
                           "retry_outcome": "aborted"})

        raise DukascopyIncompleteDataError(
            f"Dukascopy response remained incomplete for {symbol} {timeframe} {side} "
            f"on {day_start.date()}; ingestion aborted for review. "
            f"See preserved raw artifacts and provenance in {run_dir}. "
            f"Validation: {json.dumps(last_validation, sort_keys=True)}")

    async def fetch_range(self, symbol: str, timeframe: str, start: datetime,
                          end: datetime) -> AsyncIterator[OHLCObservation]:
        normalized = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
        if normalized not in self.instruments:
            raise ValueError(f"Unsupported Dukascopy instrument: {symbol}")
        if timeframe not in self.timeframes:
            raise ValueError(f"Unsupported Dukascopy timeframe: {timeframe}")
        observation_timeframe = cast(Literal["M1", "M15", "H1"], timeframe)
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("start and end must be timezone-aware with start < end")

        start_utc, end_utc = start.astimezone(UTC), end.astimezone(UTC)
        expected_all = self.expected_timestamps(start_utc, end_utc, timeframe)
        if not expected_all:
            return

        run_id = uuid.uuid4().hex
        run_dir = self.cache_directory / "raw" / f"{normalized}-{timeframe}-{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        observations: list[OHLCObservation] = []

        # Download both sides and validate every daily artifact before yielding
        # anything. The shared ingestion service therefore cannot receive a
        # partial range if a later day fails validation.
        for side in ("bid", "ask"):
            side_expected = list(expected_all)
            expected_by_day: dict[date, list[datetime]] = {}
            for stamp in side_expected:
                expected_by_day.setdefault(stamp.date(), []).append(stamp)
            side_rows: list[dict[str, Any]] = []
            side_attempts: list[dict[str, Any]] = []
            versions: list[str] = []
            for day, day_expected in sorted(expected_by_day.items()):
                day_start = datetime.combine(day, time.min, UTC)
                day_end = day_start + timedelta(days=1)
                request_start = max(start_utc, day_start)
                request_end = min(end_utc, day_end)
                daily_rows, summary, version = await self._request_daily(
                    symbol=normalized, timeframe=timeframe, side=side,
                    day_start=request_start, day_end=request_end, expected=day_expected,
                    requested_start=start_utc, requested_end=end_utc,
                    range_expected_count=len(expected_all),
                    run_dir=run_dir)
                side_rows.extend(daily_rows)
                side_attempts.append({"date": day.isoformat(), **summary})
                if version != "unknown":
                    versions.append(version)

            side_expected_set = set(side_expected)
            downloaded_stamps = [self._timestamp(row) for row in side_rows]
            missing = sorted(side_expected_set - set(downloaded_stamps))
            if missing or len(downloaded_stamps) != len(set(downloaded_stamps)):
                raise DukascopyIncompleteDataError(
                    f"Dukascopy range validation failed for {normalized} {timeframe} {side}; "
                    f"missing={[stamp.isoformat() for stamp in missing]}")
            side_artifacts = [artifact for day in side_attempts for artifact in day["attempts"]]
            provenance = {
                "provider": self.name,
                "cli_version": versions[-1] if versions else "unknown",
                "instrument": self.instruments[normalized],
                "symbol": normalized,
                "timeframe": timeframe,
                "price_side": side,
                "requested_start_utc": start_utc.isoformat(),
                "requested_end_utc_exclusive": end_utc.isoformat(),
                "request_count": sum(day["request_count"] for day in side_attempts),
                "retry_count": sum(day["retry_count"] for day in side_attempts),
                "downloaded_observation_count": len(side_rows),
                "expected_observation_count": len(side_expected),
                "missing_timestamps": [],
                "validation_status": "passed",
                "raw_artifact_location": str(run_dir),
                "raw_artifacts": side_artifacts,
                "daily_request_summary": side_attempts,
            }
            for row in side_rows:
                stamp = self._timestamp(row)
                volume = row.get("volume")
                observations.append(OHLCObservation(
                    symbol=normalized, timeframe=observation_timeframe,
                    price_side=side, timestamp=stamp,
                    open=row["open"], high=row["high"], low=row["low"], close=row["close"],
                    volume=volume,
                    volume_type=(f"dukascopy_{get_settings().market_data.dukascopy_volume_units}"
                                 if volume is not None else None),
                    source=self.name,
                    source_metadata={**provenance, "dukascopy_timestamp_ms": row["timestamp"]},
                ))

        observations.sort(key=lambda item: ((0 if item.price_side == "bid" else 1), item.timestamp))
        for observation in observations:
            yield observation
