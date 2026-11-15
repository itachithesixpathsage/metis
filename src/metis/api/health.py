"""
Health check endpoints for Project Métis.

Provides basic health and readiness checks for the API.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from metis.core.config import get_settings
from metis.core.database import get_db_session
from metis.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    timestamp: datetime
    checks: dict[str, Any]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Basic health check endpoint",
)
async def health_check() -> HealthResponse:
    """Return basic health status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Check if the service is ready to accept requests",
)
async def readiness_check(
    db_session: AsyncSession = Depends(get_db_session),
) -> ReadinessResponse:
    """Check service readiness including database connectivity."""
    checks = {}
    ready = True

    # Check database connectivity
    try:
        await db_session.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "detail": "Connected"}
    except Exception as e:
        checks["database"] = {"status": "failed", "detail": str(e)}
        ready = False

    # Check configuration
    try:
        _ = settings.database.async_url
        checks["configuration"] = {"status": "ok", "detail": "Loaded"}
    except Exception as e:
        checks["configuration"] = {"status": "failed", "detail": str(e)}
        ready = False

    if not ready:
        logger.warning("Readiness check failed", extra={"checks": checks})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )

    return ReadinessResponse(
        ready=ready,
        timestamp=datetime.now(timezone.utc),
        checks=checks,
    )