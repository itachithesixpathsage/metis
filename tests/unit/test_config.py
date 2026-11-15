"""
Unit tests for core configuration module.
"""

import pytest
from metis.core.config import (
    Settings,
    DatabaseSettings,
    APISettings,
    SimulationSettings,
    MarketDataSettings,
    LoggingSettings,
    get_settings,
)


class TestDatabaseSettings:
    """Test database configuration."""

    def test_default_values(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.username == "metis"
        assert settings.password == "metis_dev_password"
        assert settings.name == "metis"
        assert settings.pool_size == 10

    def test_async_url_property(self):
        """Test async URL generation."""
        settings = DatabaseSettings(
            host="db.example.com",
            port=5433,
            username="user",
            password="pass",
            name="mydb",
        )
        expected = "postgresql+asyncpg://user:pass@db.example.com:5433/mydb"
        assert settings.async_url == expected

    def test_sync_url_property(self):
        """Test sync URL generation."""
        settings = DatabaseSettings(
            host="db.example.com",
            port=5433,
            username="user",
            password="pass",
            name="mydb",
        )
        expected = "postgresql+psycopg2://user:pass@db.example.com:5433/mydb"
        assert settings.sync_url == expected


class TestAPISettings:
    """Test API configuration."""

    def test_default_values(self):
        """Test default API settings."""
        settings = APISettings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.api_prefix == "/api/v1"
        assert "http://localhost:5173" in settings.cors_origins


class TestSimulationSettings:
    """Test simulation configuration."""

    def test_default_values(self):
        """Test default simulation settings."""
        settings = SimulationSettings()
        assert settings.default_paths == 10_000
        assert settings.default_horizon_bars == 16
        assert settings.default_confidence_levels == [0.95, 0.99]
        assert settings.default_seed == 42
        assert settings.default_dt == 1.0 / 96.0


class TestMarketDataSettings:
    """Test market data configuration."""

    def test_default_symbols(self):
        """Test default FX symbols."""
        settings = MarketDataSettings()
        expected = [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCHF",
            "USDCAD",
            "NZDUSD",
        ]
        assert settings.default_symbols == expected

    def test_supported_frequencies(self):
        """Test supported frequencies."""
        settings = MarketDataSettings()
        assert settings.supported_frequencies == ["5min", "15min", "1h"]


class TestLoggingSettings:
    """Test logging configuration."""

    def test_default_values(self):
        """Test default logging settings."""
        settings = LoggingSettings()
        assert settings.level == "INFO"
        assert settings.json_format is True
        assert settings.include_trace_id is True


class TestMainSettings:
    """Test main application settings."""

    def test_default_values(self):
        """Test default main settings."""
        settings = Settings()
        assert settings.app_name == "Project Métis"
        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.debug is True

    def test_nested_settings(self):
        """Test nested settings are initialized."""
        settings = Settings()
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.simulation, SimulationSettings)
        assert isinstance(settings.market_data, MarketDataSettings)
        assert isinstance(settings.logging, LoggingSettings)

    def test_get_settings_cached(self):
        """Test get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestEnvironmentOverride:
    """Test environment variable overrides."""

    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("METIS_APP_NAME", "Custom Name")
        monkeypatch.setenv("METIS_API_PORT", "9000")
        monkeypatch.setenv("METIS_DB_PASSWORD", "secret123")

        settings = Settings()
        assert settings.app_name == "Custom Name"
        assert settings.api.port == 9000
        assert settings.database.password == "secret123"