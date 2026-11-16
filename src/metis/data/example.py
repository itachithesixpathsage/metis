"""Minimal deterministic ingestion example for an application supplied provider."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from metis.data.provider import HistoricalProvider
from metis.data.service import HistoricalDataService


async def ingest_eurusd_m15(session: AsyncSession, provider: HistoricalProvider):
    """Ingest one UTC date range; callers own credentialed provider construction."""
    return await HistoricalDataService(session).ingest(
        provider, "EURUSD", "M15", datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 2, 1, tzinfo=timezone.utc),
    )
