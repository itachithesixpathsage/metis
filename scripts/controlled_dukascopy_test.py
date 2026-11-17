#!/usr/bin/env python3
"""Controlled five-day Dukascopy ingestion check (never a bulk backfill).

Default range is 2026-11-09 through 2026-11-14 UTC, half-open. The script
downloads once, replays those exact provider observations through the standard
ingestion service twice, and checks persistence/idempotency without refetching.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shlex
import shutil
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from metis.core.database import db_manager  # noqa: E402
from metis.core.config import get_settings  # noqa: E402
from metis.data.dukascopy import DukascopyProvider  # noqa: E402
from metis.data.provider import HistoricalProvider  # noqa: E402
from metis.data.schemas import OHLCObservation  # noqa: E402
from metis.data.service import HistoricalDataService  # noqa: E402


class ReplayProvider(HistoricalProvider):
    name = "dukascopy"

    def __init__(self, observations: list[OHLCObservation]):
        self.observations = observations

    async def fetch_range(self, symbol, timeframe, start, end):
        for item in self.observations:
            yield item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-11-09", help="UTC inclusive date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-11-14", help="UTC exclusive date (YYYY-MM-DD)")
    parser.add_argument("--max-days", type=int, default=7,
                        help="Safety cap on range length; values above 7 are rejected")
    return parser.parse_args()


def trading_gap_count(rows: list[OHLCObservation]) -> int:
    """Count missing one-minute starts during weekdays, excluding the FX weekend."""
    by_side: dict[str, list[datetime]] = {}
    for row in rows:
        by_side.setdefault(row.price_side, []).append(row.timestamp)
    gaps = 0
    for stamps in by_side.values():
        stamps = sorted(set(stamps))
        for before, after in zip(stamps, stamps[1:]):
            cursor = before + timedelta(minutes=1)
            while cursor < after:
                if cursor.weekday() < 5:
                    gaps += 1
                cursor += timedelta(minutes=1)
    return gaps


async def run() -> dict:
    args = parse_args()
    start_date, end_date = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end_date <= start_date or (end_date - start_date).days > min(args.max_days, 7):
        raise ValueError("Date range must be positive and no longer than seven days")
    start = datetime.combine(start_date, time.min, timezone.utc)
    end = datetime.combine(end_date, time.min, timezone.utc)
    settings = get_settings()
    executable = settings.market_data.dukascopy_executable
    command = shlex.split(executable)
    resolved_command = shutil.which(command[0]) if command else None
    if not resolved_command and command and Path(command[0]).is_file():
        resolved_command = str(Path(command[0]).resolve())
    if not resolved_command:
        raise RuntimeError(f"Dukascopy CLI not found: {executable}")
    command[0] = resolved_command
    executable = shlex.join(command)

    observations = [item async for item in DukascopyProvider(executable=executable).fetch_range(
        "EURUSD", "M1", start, end)]
    downloaded = len(observations)
    sides = Counter(item.price_side for item in observations)
    provider = ReplayProvider(observations)

    db_manager.initialize()
    try:
        async with db_manager.session() as session:
            service = HistoricalDataService(session)
            before = {side: await service.retrieve("EURUSD", "M1", start, end, side)
                      for side in ("bid", "ask")}
            first_report = await service.ingest(provider, "EURUSD", "M1", start, end)
            after_first = {side: await service.retrieve("EURUSD", "M1", start, end, side)
                           for side in ("bid", "ask")}
            second_report = await service.ingest(provider, "EURUSD", "M1", start, end)
            after_second = {side: await service.retrieve("EURUSD", "M1", start, end, side)
                            for side in ("bid", "ask")}

        bid_map = {r.timestamp: r for r in after_first["bid"]}
        ask_map = {r.timestamp: r for r in after_first["ask"]}
        common = sorted(bid_map.keys() & ask_map.keys())
        crossed_or_locked = sum(ask_map[t].close <= bid_map[t].close for t in common)
        utc_ok = all(r.timestamp.tzinfo == timezone.utc for rs in after_first.values() for r in rs)
        idempotent = all(len(after_first[s]) == len(after_second[s]) for s in ("bid", "ask"))
        counts_unchanged = all(len(before[s]) <= len(after_first[s]) for s in ("bid", "ask"))
        result = {
            "instrument": "EURUSD", "timeframe": "M1", "range_start_utc": start.isoformat(),
            "range_end_utc_exclusive": end.isoformat(), "cli_command": executable,
            "rows_downloaded": downloaded, "downloaded_by_side": dict(sides),
            "accepted": len(first_report.accepted), "rejected_invalid": len(first_report.invalid),
            "flagged_suspicious": len(first_report.suspicious),
            "duplicates_within_download": len(first_report.duplicates),
            "out_of_order": len(first_report.out_of_order),
            "persisted_valid_by_side": {s: len(after_first[s]) for s in ("bid", "ask")},
            "preexisting_by_side": {s: len(before[s]) for s in ("bid", "ask")},
            "idempotent_second_ingestion": idempotent and counts_unchanged,
            "utc_timestamps": utc_ok,
            "matched_bid_ask_timestamps": len(common),
            "unmatched_bid": len(set(bid_map) - set(ask_map)),
            "unmatched_ask": len(set(ask_map) - set(bid_map)),
            "ask_not_above_bid_close_count": crossed_or_locked,
            "weekday_minute_gaps": trading_gap_count([*after_first["bid"], *after_first["ask"]]),
            "actual_coverage_by_side": {
                s: {"first_utc": min((r.timestamp for r in after_first[s]), default=None),
                    "last_utc": max((r.timestamp for r in after_first[s]), default=None)}
                for s in ("bid", "ask")
            },
            "ohlc_valid": True,
        }
        result["actual_coverage_by_side"] = {
            s: {k: v.isoformat() if v else None for k, v in bounds.items()}
            for s, bounds in result["actual_coverage_by_side"].items()
        }
        result["ohlc_valid"] = all(
            r.high >= max(r.open, r.close, r.low) and r.low <= min(r.open, r.close, r.high)
            for rs in after_first.values() for r in rs)
        print(json.dumps(result, indent=2))
        if not downloaded or not after_first["bid"] or not after_first["ask"]:
            raise RuntimeError("Provider returned no persisted observations for one or both sides")
        if not utc_ok or not result["ohlc_valid"] or not idempotent:
            raise RuntimeError("Post-ingestion integrity check failed")
        return result
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run())
