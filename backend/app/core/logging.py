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
    Includes sensitive data sanitization for security.
    """

    # Fields that may contain sensitive information
    _SENSITIVE_FIELDS = {
        "password",
        "token",
        "secret",
        "key",
        "authorization",
        "auth",
        "cookie",
        "session",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
    }

    def _sanitize_value(self, key: str, value: Any) -> Any:
        """Sanitize sensitive values in log data.

        Args:
            key: Field name
            value: Field value

        Returns:
            Sanitized value (masked if sensitive)
        """
        if value is None:
            return value

        # Check if key contains sensitive keywords
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in self._SENSITIVE_FIELDS):
            if isinstance(value, str):
                if len(value) > 8:
                    return f"{value[:4]}****{value[-4:]}"
                return "****"
            return "****"

        # Recursively sanitize dictionaries
        if isinstance(value, dict):
            return {k: self._sanitize_value(k, v) for k, v in value.items()}

        # Recursively sanitize lists
        if isinstance(value, list):
            return [self._sanitize_value(f"{key}[{i}]", item) for i, item in enumerate(value)]

        return value

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
            "message": self._sanitize_value("message", record.getMessage()),
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
                exc_message = str(exc_value) if exc_value else ""
                log_data["otel"] = {
                    "exception.type": exc_type.__name__,
                    "exception.message": self._sanitize_value("exception.message", exc_message),
                }
                if exc_traceback:
                    # Stack traces are usually safe, but sanitize message parts
                    stacktrace = self.formatException(record.exc_info)
                    log_data["otel"]["exception.stacktrace"] = stacktrace

        # Add structured data (RFC 5424 SD) with sanitization
        if hasattr(record, "sd") and record.sd:
            log_data["sd"] = self._sanitize_value("sd", record.sd)

        # Add any extra fields with sanitization
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
                log_data[key] = self._sanitize_value(key, value)

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
