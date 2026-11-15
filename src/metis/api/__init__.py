"""
FastAPI application factory for Project Métis.

Creates and configures the FastAPI application with all routes and middleware.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from metis.core.config import get_settings
from metis.core.database import db_manager
from metis.core.logging import setup_logging, get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Project Métis", extra={"version": settings.app_version})
    setup_logging()
    db_manager.initialize()
    logger.info("Project Métis startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Project Métis")
    await db_manager.close()
    logger.info("Project Métis shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Quantitative FX Research & Portfolio Risk Intelligence Platform",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from metis.api.health import router as health_router
    app.include_router(health_router, prefix=settings.api.api_prefix)

    return app