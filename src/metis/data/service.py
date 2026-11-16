"""Ingestion, persistence, and validated retrieval service."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from metis.data.provider import HistoricalProvider, fetch_with_retries
from metis.data.schemas import OHLCObservation
from metis.data.validation import QualityReport, validate_observations
from metis.models.historical import HistoricalBar


class HistoricalDataService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ingest(self, provider: HistoricalProvider, symbol: str, timeframe: str,
                     start: datetime, end: datetime) -> QualityReport:
        received = []
        invalid = []
        async for raw in fetch_with_retries(provider, symbol, timeframe, start, end):
            try:
                received.append(raw if isinstance(raw, OHLCObservation) else OHLCObservation.model_validate(raw))
            except Exception as exc:
                invalid.append((raw if isinstance(raw, dict) else {"value": repr(raw)}, str(exc)))
        report = validate_observations(received)
        report.invalid.extend(invalid)
        if report.accepted:
            values = [dict(symbol=x.symbol, timestamp=x.timestamp, timeframe=x.timeframe,
                           open=x.open, high=x.high, low=x.low, close=x.close, volume=x.volume,
                           volume_type=x.volume_type, source=x.source, ingested_at=x.ingested_at,
                           source_metadata=x.source_metadata) for x in report.accepted]
            dialect = self.session.get_bind().dialect.name
            insert_statement = sqlite_insert if dialect == "sqlite" else pg_insert
            statement = insert_statement(HistoricalBar).values(values).on_conflict_do_nothing(
                index_elements=["symbol", "timeframe", "timestamp"])
            await self.session.execute(statement)
        rejected = [dict(symbol=item.symbol if isinstance(item, OHLCObservation) else "UNKNOWN",
                         timestamp=item.timestamp if isinstance(item, OHLCObservation) else start,
                         timeframe=timeframe, source=provider.name,
                         ingested_at=datetime.now(timezone.utc),
                         source_metadata={"reason": reason, "observation": item.model_dump(mode="json")
                                          if isinstance(item, OHLCObservation) else item},
                         quality_status="suspicious" if isinstance(item, OHLCObservation) else "invalid")
                    for item, reason in [*report.suspicious, *report.invalid]]
        if rejected:
            dialect = self.session.get_bind().dialect.name
            insert_statement = sqlite_insert if dialect == "sqlite" else pg_insert
            await self.session.execute(insert_statement(HistoricalBar).values(rejected).on_conflict_do_nothing(
                index_elements=["symbol", "timeframe", "timestamp"]))
        if report.accepted or rejected:
            await self.session.commit()
        return report

    async def retrieve(self, symbol: str, timeframe: str, start: datetime,
                       end: datetime) -> list[OHLCObservation]:
        rows = (await self.session.scalars(select(HistoricalBar).where(
            HistoricalBar.symbol == symbol.upper().replace("/", "").replace("-", "").replace("_", ""),
            HistoricalBar.timeframe == timeframe, HistoricalBar.timestamp >= start,
            HistoricalBar.timestamp < end, HistoricalBar.quality_status == "valid",
        ).order_by(HistoricalBar.timestamp))).all()
        return [OHLCObservation.model_validate({k: getattr(row, k) for k in (
            "symbol", "timestamp", "timeframe", "open", "high", "low", "close", "volume",
            "volume_type", "source", "ingested_at", "source_metadata")}) for row in rows]
