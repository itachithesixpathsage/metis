"""Validated historical data retrieval API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from metis.core.database import get_db_session
from metis.data.schemas import OHLCObservation
from metis.data.service import HistoricalDataService

router = APIRouter(prefix="/historical-data", tags=["historical data"])


class DatasetResponse(BaseModel):
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    observations: list[OHLCObservation]


@router.get("/{symbol}", response_model=DatasetResponse,
            summary="Retrieve validated historical Forex OHLC observations")
async def get_dataset(symbol: str, timeframe: str = Query(pattern="^(M15|H1)$"),
                      start: datetime = Query(), end: datetime = Query(),
                      session: AsyncSession = Depends(get_db_session)) -> DatasetResponse:
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise HTTPException(status_code=422, detail="start/end must be timezone-aware and start < end")
    records = await HistoricalDataService(session).retrieve(symbol, timeframe, start, end)
    return DatasetResponse(symbol=symbol.upper().replace("/", "").replace("-", "").replace("_", ""),
                           timeframe=timeframe, start=start, end=end, observations=records)
