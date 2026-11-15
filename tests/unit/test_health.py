"""
Unit tests for health check API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from metis.api import create_app
from metis.core.database import get_db_session
from metis.core.config import Settings, DatabaseSettings


@pytest.fixture
def test_settings():
    """Create test settings with in-memory database."""
    return Settings(
        environment="development",
        debug=True,
        database=DatabaseSettings(
            host="localhost",
            port=5432,
            username="test",
            password="test",
            name="test",
        ),
    )


@pytest.fixture
def mock_db_session():
    """Mock database session for readiness checks."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    return mock_session


@pytest.fixture
def app(test_settings, mock_db_session):
    """Create test FastAPI app with overridden database dependency."""
    # Override the database dependency
    async def override_get_db_session():
        yield mock_db_session
    
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    """Create test async client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"
        assert data["environment"] == "development"

    @pytest.mark.asyncio
    async def test_readiness_check_success(self, client, mock_db_session):
        """Test readiness check with successful database connection."""
        response = await client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "ok"
        assert data["checks"]["configuration"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readiness_check_database_failure(self, client, mock_db_session):
        """Test readiness check with database failure."""
        mock_db_session.execute = AsyncMock(side_effect=Exception("Connection failed"))
        response = await client.get("/api/v1/ready")
        assert response.status_code == 503