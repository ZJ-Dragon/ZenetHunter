"""Structured logging configuration.

This module configures Python's logging system to produce structured JSON logs
aligned with RFC 5424 Syslog and OpenTelemetry exception semantics.

References:
- RFC 5424 Syslog: https://www.rfc-editor.org/rfc/rfc5424.html
- OpenTelemetry Logs: https://opentelemetry.io/docs/specs/semconv/general/logs/
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Produces logs in a format compatible with RFC 5424 Syslog and
    OpenTelemetry conventions, including exception semantics.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation of the log record
        """
        # Base log structure (RFC 5424 inspired)
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": self._map_severity(record.levelno),
            "module": record.module,
            "message": record.getMessage(),
        }

        # Add logger name if different from module
        if record.name != record.module:
            log_data["logger"] = record.name

        # Add correlation_id if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add exception information (OpenTelemetry semantics)
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            if exc_type:
                log_data["otel"] = {
                    "exception.type": exc_type.__name__,
                    "exception.message": str(exc_value) if exc_value else "",
                }
                if exc_traceback:
                    log_data["otel"]["exception.stacktrace"] = self.formatException(
                        record.exc_info
                    )

        # Add structured data (RFC 5424 SD)
        if hasattr(record, "sd") and record.sd:
            log_data["sd"] = record.sd

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "correlation_id",
                "sd",
            }:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


def _map_severity(levelno: int) -> str:
    """Map Python logging level to RFC 5424 severity.

    Args:
        levelno: Python logging level number

    Returns:
        RFC 5424 severity string
    """
    mapping: dict[int, str] = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "FATAL",
    }
    return mapping.get(levelno, "INFO")


def setup_logging() -> None:
    """Configure application logging.

    Sets up structured JSON logging with level from settings.
    Logs are written to stdout for container-friendly output.
    """
    settings = get_settings()

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level_int)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler (stdout for containers)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level_int)

    # Use structured formatter
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
