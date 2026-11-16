from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from metis.api import create_app
from metis.core.database import db_manager, get_db_session
from metis.data.provider import HistoricalProvider
from metis.data.schemas import OHLCObservation
from metis.data.service import HistoricalDataService


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
