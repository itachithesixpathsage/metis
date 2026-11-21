"""Provider-independent historical retrieval contract and retrying adapter."""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from metis.data.schemas import OHLCObservation


class HistoricalProvider(ABC):
    name: str

    @abstractmethod
    def fetch_range(self, symbol: str, timeframe: str, start: datetime,
                    end: datetime) -> AsyncIterator[OHLCObservation | dict[str, Any]]:
        """Return provider observations in the requested half-open range."""


async def fetch_with_retries(provider: HistoricalProvider, symbol: str, timeframe: str,
                             start: datetime, end: datetime, attempts: int = 3
                             ) -> AsyncIterator[OHLCObservation | dict[str, Any]]:
    """Retry transient provider failures; adapters own pagination and throttling."""
    for attempt in range(attempts):
        try:
            async for observation in provider.fetch_range(symbol, timeframe, start, end):
                yield observation
            return
        except Exception as exc:
            if getattr(exc, "retryable", True) is False:
                raise
            if attempt + 1 == attempts:
                raise
            await asyncio.sleep(0.1 * (2 ** attempt))
