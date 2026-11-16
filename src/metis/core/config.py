"""
Core configuration for Project Métis.

Uses Pydantic Settings for environment-based configuration management.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="METIS_DB_")

    host: str = "localhost"
    port: int = 5432
    username: str = "metis"
    password: str = "metis_dev_password"
    name: str = "metis"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @property
    def async_url(self) -> str:
        """Async SQLAlchemy URL (asyncpg)."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """Sync SQLAlchemy URL (psycopg2)."""
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class APISettings(BaseSettings):
    """API configuration."""

    model_config = SettingsConfigDict(env_prefix="METIS_API_")

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    api_prefix: str = "/api/v1"


class SimulationSettings(BaseSettings):
    """Stochastic simulation defaults."""

    model_config = SettingsConfigDict(env_prefix="METIS_SIM_")

    default_paths: int = 10_000
    default_horizon_bars: int = 16  # 4 hours at 15-min bars
    default_confidence_levels: list[float] = [0.95, 0.99]
    default_seed: int = 42
    default_dt: float = 1.0 / 96.0  # 15 minutes as fraction of trading day


class MarketDataSettings(BaseSettings):
    """Market data configuration."""

    model_config = SettingsConfigDict(env_prefix="METIS_MD_")

    default_provider: str = "synthetic"
    default_frequency: str = "15min"
    supported_frequencies: list[str] = ["5min", "15min", "1h"]
    default_symbols: list[str] = [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCHF",
        "USDCAD",
        "NZDUSD",
    ]
    validation_enabled: bool = True
    max_spread_bps: int = 50
    max_stale_minutes: int = 60
    dukascopy_executable: str = "dukascopy-node"
    dukascopy_cache_directory: str = ".cache/dukascopy-node"
    dukascopy_batch_size: int = 4
    dukascopy_batch_pause_ms: int = 1000
    dukascopy_retries: int = 3
    dukascopy_volume_units: Literal["millions", "thousands", "units"] = "units"


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="METIS_LOG_")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_format: bool = True
    include_trace_id: bool = True


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="METIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Project Métis"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    market_data: MarketDataSettings = Field(default_factory=MarketDataSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Order sources so real environment variables override the `.env` file.

        pydantic-settings merges sources with ``deep_update(source_state, state)``,
        Pydantic settings sources are ordered from highest to lowest priority.
        Keep live environment values ahead of dotenv values.
        """
        return init_settings, env_settings, dotenv_settings, file_secret_settings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export for convenience
settings = get_settings()
