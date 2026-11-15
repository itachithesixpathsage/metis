"""
Test configuration and fixtures for Project Métis.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from metis.core.config import DatabaseSettings, Settings
from metis.core.database import Base, DatabaseManager
from metis.models import TimestampMixin, UUIDMixin


# Test database URL (SQLite in-memory for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with in-memory database."""
    return Settings(
        environment="testing",
        debug=True,
        database=DatabaseSettings(
            host="localhost",
            port=5432,
            username="test",
            password="test",
            name="test",
        ),
    )


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def sample_instrument():
    """Sample FX instrument data."""
    return {
        "symbol": "EURUSD",
        "base_currency": "EUR",
        "quote_currency": "USD",
        "name": "Euro / US Dollar",
        "pip_size": Decimal("0.0001"),
        "contract_size": Decimal("100000"),
        "is_active": True,
    }


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data."""
    return {
        "name": "Test Portfolio",
        "description": "Test portfolio for unit tests",
        "reporting_currency": "USD",
        "base_currency": "USD",
        "is_active": True,
    }


@pytest.fixture
def sample_position():
    """Sample position data."""
    return {
        "direction": "LONG",
        "notional_amount": Decimal("1000000"),
        "notional_currency": "EUR",
        "entry_price": Decimal("1.0850"),
        "entry_timestamp": datetime.now(timezone.utc),
        "leverage": Decimal("1.0"),
        "transaction_cost_bps": 0,
        "is_open": True,
    }


# Statistical test fixtures
@pytest.fixture
def sample_returns():
    """Sample return series for statistical tests."""
    import numpy as np
    np.random.seed(42)
    return np.random.normal(0.0001, 0.01, 1000)


@pytest.fixture
def sample_prices():
    """Sample price series for testing."""
    import numpy as np
    np.random.seed(42)
    returns = np.random.normal(0.0001, 0.01, 1000)
    prices = 1.0850 * np.exp(np.cumsum(returns))
    return prices


# Simulation test fixtures
@pytest.fixture
def gbm_parameters():
    """GBM simulation parameters."""
    return {
        "drift": 0.0,
        "volatility": 0.10,
        "initial_price": 1.0850,
        "dt": 1.0 / 96.0,
        "num_paths": 1000,
        "num_steps": 16,
        "seed": 42,
    }


# Helper functions
def assert_close(actual: float, expected: float, rel_tol: float = 1e-6, abs_tol: float = 1e-9):
    """Assert two floats are close."""
    import math
    assert math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol), \
        f"Expected {expected}, got {actual}"


def assert_array_close(actual, expected, rel_tol: float = 1e-6, abs_tol: float = 1e-9):
    """Assert two arrays are close."""
    import numpy as np
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    assert actual.shape == expected.shape, f"Shape mismatch: {actual.shape} vs {expected.shape}"
    assert np.allclose(actual, expected, rtol=rel_tol, atol=abs_tol), \
        f"Arrays not close:\nActual: {actual}\nExpected: {expected}"