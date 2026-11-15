"""
Logging configuration for Project Métis.

Provides structured JSON logging with trace ID support.
"""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from metis.core.config import get_settings


class TraceIDFilter(logging.Filter):
    """Filter to add trace ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = "N/A"
        return True


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.logging.level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.logging.level)

    if settings.logging.json_format:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(trace_id)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
            rename_fields={
                "asctime": "timestamp",
                "name": "logger",
                "levelname": "level",
                "trace_id": "trace_id",
                "message": "message",
            },
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(trace_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    console_handler.addFilter(TraceIDFilter())
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database.echo else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)