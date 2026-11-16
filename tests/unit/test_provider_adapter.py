from datetime import datetime, timedelta, timezone

import pytest

from metis.data.provider import HistoricalProvider, fetch_with_retries
from metis.data.schemas import OHLCObservation


class PagedProvider(HistoricalProvider):
    name = "paged-test"

    def __init__(self):
        self.calls = 0
        self.waits = []

    async def fetch_range(self, symbol, timeframe, start, end):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("429 rate limited")
        # Adapter example: paging and Retry-After delay are adapter responsibilities.
        self.waits.append(0.25)
        for page in range(2):
            yield OHLCObservation(symbol=symbol, timeframe=timeframe,
                timestamp=start + timedelta(minutes=15 * page), open=1.1, high=1.2,
                low=1.0, close=1.1, source=self.name,
                source_metadata={"page": page + 1})


@pytest.mark.asyncio
async def test_retry_adapter_yields_paged_observations(monkeypatch):
    provider = PagedProvider()
    delays = []
    async def fake_sleep(delay):
        delays.append(delay)
    monkeypatch.setattr("metis.data.provider.asyncio.sleep", fake_sleep)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [r async for r in fetch_with_retries(provider, "EURUSD", "M15", start,
                                                  start + timedelta(hours=1))]
    assert provider.calls == 2
    assert delays == [0.1]
    assert [r.source_metadata["page"] for r in rows] == [1, 2]
