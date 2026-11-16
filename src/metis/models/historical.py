"""Persisted validated Forex OHLC bars."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import Mapped, mapped_column

from metis.models import Base


class HistoricalBar(Base):
    __tablename__ = "historical_bars"

    @declared_attr.directive
    def __table_args__(cls):
        constraints = (
            UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_historical_bar"),
            Index("ix_historical_bars_query", "symbol", "timeframe", "timestamp"),
        )
        return constraints + (({"schema": "market_data"},) if cls.metadata.info.get("use_market_schema", True) else ())

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(6), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(3), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=False, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float | None] = mapped_column(Float)
    volume_type: Mapped[str | None] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    quality_status: Mapped[str] = mapped_column(String(16), nullable=False, default="valid")
