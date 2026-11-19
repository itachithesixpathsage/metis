from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from metis.api import create_app
from metis.core.database import db_manager, get_db_session
from metis.data.provider import HistoricalProvider
from metis.data.schemas import OHLCObservation
from metis.data.service import HistoricalDataService
import metis.data.service as historical_service


class SampleProvider(HistoricalProvider):
    name = "integration-fixture"

    def __init__(self, observations):
        self.observations = observations

    async def fetch_range(self, symbol, timeframe, start, end):
        for item in self.observations:
            yield item


@pytest.mark.asyncio
async def test_database_ingestion_is_idempotent_and_retrievable(db_session):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    row = OHLCObservation(symbol="EURUSD", timeframe="M15", timestamp=start,
                          open=1.1, high=1.2, low=1.0, close=1.1, source="fixture")
    service = HistoricalDataService(db_session)
    provider = SampleProvider([row])
    await service.ingest(provider, "EURUSD", "M15", start, start + timedelta(hours=1))
    await service.ingest(provider, "EURUSD", "M15", start, start + timedelta(hours=1))
    result = await service.retrieve("EURUSD", "M15", start, start + timedelta(hours=1))
    assert len(result) == 1
    assert result[0].source == "fixture"


@pytest.mark.asyncio
async def test_bid_and_ask_share_timestamp_and_retrieve_independently(db_session):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [
        OHLCObservation(symbol="EURUSD", timeframe="M1", price_side=side, timestamp=start,
                        open=price, high=price + .001, low=price - .001,
                        close=price, source="fixture")
        for side, price in (("bid", 1.1000), ("ask", 1.1002))
    ]
    service = HistoricalDataService(db_session)
    await service.ingest(SampleProvider(rows), "EURUSD", "M1", start, start + timedelta(minutes=2))
    bid = await service.retrieve("EURUSD", "M1", start, start + timedelta(minutes=2), "bid")
    ask = await service.retrieve("EURUSD", "M1", start, start + timedelta(minutes=2), "ask")
    unspecified = await service.retrieve("EURUSD", "M1", start, start + timedelta(minutes=2))
    assert len(bid) == len(ask) == 1
    assert bid[0].close == 1.1
    assert ask[0].close == 1.1002
    assert unspecified == []


@pytest.mark.asyncio
async def test_ingestion_chunks_large_insert_batches(db_session, monkeypatch):
    """Keep bulk inserts below database bind-parameter limits."""
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [
        OHLCObservation(symbol="EURUSD", timeframe="M1", timestamp=start + timedelta(minutes=i),
                        open=1.1, high=1.101, low=1.099, close=1.1, source="fixture")
        for i in range(5)
    ]
    monkeypatch.setattr(historical_service, "_INSERT_BATCH_SIZE", 2)
    service = HistoricalDataService(db_session)

    report = await service.ingest(SampleProvider(rows), "EURUSD", "M1", start,
                                  start + timedelta(minutes=5))
    stored = await service.retrieve("EURUSD", "M1", start, start + timedelta(minutes=5))

    assert len(report.accepted) == 5
    assert len(stored) == 5


@pytest.mark.asyncio
async def test_dataset_api_returns_validated_rows(db_session, monkeypatch):
    async def override_session():
        yield db_session
    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    provider = SampleProvider([OHLCObservation(symbol="EURUSD", timeframe="H1", timestamp=start,
        open=1.1, high=1.2, low=1.0, close=1.1, source="fixture")])
    await HistoricalDataService(db_session).ingest(provider, "EURUSD", "H1", start,
                                                    start + timedelta(hours=2))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/historical-data/EURUSD", params={
            "timeframe": "H1", "start": start.isoformat(),
            "end": (start + timedelta(hours=2)).isoformat()})
    assert response.status_code == 200
    assert len(response.json()["observations"]) == 1
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dataset_api_requires_explicit_filter_to_retrieve_bid_or_ask(db_session):
    async def override_session():
        yield db_session
    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [OHLCObservation(symbol="EURUSD", timeframe="M15", price_side=side,
        timestamp=start, open=1.1, high=1.2, low=1.0, close=1.1, source="fixture")
        for side in ("bid", "ask")]
    await HistoricalDataService(db_session).ingest(SampleProvider(rows), "EURUSD", "M15",
        start, start + timedelta(hours=1))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/historical-data/EURUSD", params={
            "timeframe": "M15", "price_side": "bid", "start": start.isoformat(),
            "end": (start + timedelta(hours=1)).isoformat()})
    assert response.status_code == 200
    assert [item["price_side"] for item in response.json()["observations"]] == ["bid"]
    app.dependency_overrides.clear()
