import json
from datetime import datetime, timedelta, timezone

import pytest

from metis.data.dukascopy import DukascopyProvider


@pytest.mark.asyncio
async def test_fetches_bid_and_ask_independently_and_maps_utc_candles(tmp_path):
    calls = []
    stamp = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    async def runner(args):
        calls.append(args)
        side = args[args.index("-p") + 1]
        return json.dumps([{"timestamp": stamp, "open": 1.1, "high": 1.2,
                            "low": 1.0, "close": 1.1, "volume": 12.0}])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [row async for row in provider.fetch_range("EUR/USD", "M1", start,
                                                       start + timedelta(minutes=1))]
    assert [row.price_side for row in rows] == ["bid", "ask"]
    assert all(row.timestamp == start and row.timestamp.tzinfo == timezone.utc for row in rows)
    assert rows[0].volume_type
    assert calls[0][calls[0].index("-t") + 1] == "m1"
    assert calls[0][:2] == ["npx", "dukascopy-node"]
    assert calls[1][calls[1].index("-p") + 1] == "ask"


@pytest.mark.asyncio
async def test_rejects_unsupported_instrument_and_timeframe(tmp_path):
    provider = DukascopyProvider(cache_directory=tmp_path, runner=lambda _: "[]")
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        _ = [row async for row in provider.fetch_range("AUDUSD", "M1", start, start + timedelta(days=1))]
