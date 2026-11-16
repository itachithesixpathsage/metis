"""Canonical historical OHLC contracts."""

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OHLCObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp: datetime
    timeframe: Literal["M15", "H1"]
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    volume_type: str | None = None
    source: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        symbol = value.upper().replace("/", "").replace("_", "").replace("-", "")
        if len(symbol) != 6 or not symbol.isalpha():
            raise ValueError("symbol must contain two three-letter currency codes")
        return symbol

    @field_validator("timestamp", "ingested_at")
    @classmethod
    def utc_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def valid_prices(self) -> "OHLCObservation":
        values = (self.open, self.high, self.low, self.close)
        if not all(isfinite(value) and value > 0 for value in values):
            raise ValueError("OHLC prices must be finite and positive")
        if self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close, self.high):
            raise ValueError("invalid OHLC relationship")
        return self
