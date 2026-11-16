"""Dukascopy historical candle adapter using the documented dukascopy-node CLI."""

import asyncio
import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from metis.core.config import get_settings
from metis.data.provider import HistoricalProvider
from metis.data.schemas import OHLCObservation

logger = logging.getLogger(__name__)


class DukascopyProvider(HistoricalProvider):
    name = "dukascopy"
    instruments = {"EURUSD": "eurusd", "GBPUSD": "gbpusd", "USDJPY": "usdjpy"}
    timeframes = {"M1": "m1", "M15": "m15", "H1": "h1"}

    def __init__(self, executable: str | None = None, cache_directory: str | Path | None = None,
                 batch_size: int | None = None, batch_pause_ms: int | None = None,
                 retries: int | None = None, runner: Any = None):
        settings = get_settings().market_data
        self.executable = executable or settings.dukascopy_executable
        self.cache_directory = Path(cache_directory or settings.dukascopy_cache_directory)
        self.batch_size = batch_size or settings.dukascopy_batch_size
        self.batch_pause_ms = batch_pause_ms if batch_pause_ms is not None else settings.dukascopy_batch_pause_ms
        self.retries = retries or settings.dukascopy_retries
        self._runner = runner or self._run

    async def _run(self, args: list[str]) -> str:
        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(f"dukascopy-node failed ({process.returncode}): {stderr.decode(errors='replace')}")
        output_path = Path(args[args.index("-dir") + 1]) / f"{args[args.index('-fn') + 1]}.json"
        if not output_path.exists():
            raise RuntimeError(f"dukascopy-node did not create expected output file: {output_path.name}")
        return output_path.read_text(encoding="utf-8")

    @staticmethod
    def _parse_json(payload: str) -> list[dict[str, Any]]:
        text = payload.strip()
        if not text:
            return []
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # CLI progress may precede JSON on stdout; use the final JSON line/block.
            start = min((i for i in (text.find("["), text.find("{")) if i >= 0), default=-1)
            if start < 0:
                raise ValueError("dukascopy-node returned no JSON candle data")
            result = json.loads(text[start:])
        if isinstance(result, dict):
            result = result.get("data", result.get("candles", [result]))
        if not isinstance(result, list) or not all(isinstance(row, dict) for row in result):
            raise ValueError("dukascopy-node JSON must contain a list of candle objects")
        return result

    async def fetch_range(self, symbol: str, timeframe: str, start: datetime,
                          end: datetime) -> AsyncIterator[OHLCObservation]:
        normalized = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
        if normalized not in self.instruments:
            raise ValueError(f"Unsupported Dukascopy instrument: {symbol}")
        if timeframe not in self.timeframes:
            raise ValueError(f"Unsupported Dukascopy timeframe: {timeframe}")
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("start and end must be timezone-aware with start < end")
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        for side in ("bid", "ask"):
            with tempfile.TemporaryDirectory(prefix="metis-dukascopy-") as output_dir:
                args = [self.executable, "-i", self.instruments[normalized],
                    "-from", start.astimezone(timezone.utc).isoformat(timespec="seconds"),
                    "-to", end.astimezone(timezone.utc).isoformat(timespec="seconds"),
                    "-t", self.timeframes[timeframe], "-p", side, "-utc", "0",
                    "-f", "json", "-v", "-vu", get_settings().market_data.dukascopy_volume_units,
                    "-dir", output_dir, "-fn", f"{normalized}-{timeframe}-{side}",
                    "--cache", "--cache-path", str(self.cache_directory),
                    "--retries", str(self.retries), "--batch-size", str(self.batch_size),
                    "--batch-pause", str(self.batch_pause_ms)]
                raw = await self._runner(args)
                rows = self._parse_json(raw)
                for row in rows:
                    stamp = datetime.fromtimestamp(float(row["timestamp"]) / 1000, timezone.utc)
                    if not (start.astimezone(timezone.utc) <= stamp < end.astimezone(timezone.utc)):
                        continue
                    volume = row.get("volume")
                    yield OHLCObservation(symbol=normalized, timeframe=timeframe, price_side=side,
                        timestamp=stamp, open=row["open"], high=row["high"], low=row["low"],
                        close=row["close"], volume=volume,
                        volume_type=f"dukascopy_{get_settings().market_data.dukascopy_volume_units}" if volume is not None else None,
                        source=self.name, source_metadata={"provider": self.name,
                            "instrument": self.instruments[normalized], "price_side": side,
                            "dukascopy_timestamp_ms": row["timestamp"]})
