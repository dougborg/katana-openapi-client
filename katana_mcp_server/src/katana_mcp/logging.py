"""Structured logging configuration for Katana MCP Server.

This module provides structured logging using structlog with contextual information,
trace IDs, and performance metrics.

Features:
- JSON or text (console) output formats
- Configurable log levels via environment
- Trace ID support for request correlation
- Performance metrics (duration, counts)
- Error context with stack traces
- No sensitive data logging (API keys, credentials)

Environment Variables:
- KATANA_MCP_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR) - default INFO
- KATANA_MCP_LOG_FORMAT: Output format (json, text) - default json

Example Usage:
    from katana_mcp.logging import get_logger

    logger = get_logger()
    logger.info("tool_executed", tool_name="search_items", result_count=15)
"""

from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar

import structlog
from structlog.typing import EventDict, WrappedLogger

# Context variable for trace IDs
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def add_trace_id(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add trace ID to log events if available.

    Args:
        logger: The wrapped logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary to modify

    Returns:
        Modified event dictionary with trace_id if available
    """
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def filter_sensitive_data(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Filter sensitive data from logs.

    Removes or redacts API keys, credentials, and other sensitive information.

    Args:
        logger: The wrapped logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary to modify

    Returns:
        Modified event dictionary with sensitive data filtered
    """
    # List of sensitive keys to redact
    sensitive_keys = {
        "api_key",
        "password",
        "secret",
        "token",
        "auth",
        "credential",
        "authorization",
    }

    # Redact sensitive keys (case-insensitive)
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***REDACTED***"

    return event_dict


def setup_logging(log_level: str | None = None, log_format: str | None = None) -> None:
    """Configure structured logging for MCP server.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR).
                  If None, reads from KATANA_MCP_LOG_LEVEL env var.
                  Defaults to INFO.
        log_format: Output format (json or text).
                   If None, reads from KATANA_MCP_LOG_FORMAT env var.
                   Defaults to json.
    """
    # Get configuration from environment or parameters
    level = log_level or os.getenv("KATANA_MCP_LOG_LEVEL", "INFO").upper()
    format_type = log_format or os.getenv("KATANA_MCP_LOG_FORMAT", "json").lower()

    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if level not in valid_levels:
        level = "INFO"

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level),
    )

    # Common processors for all formats
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_trace_id,
        filter_sensitive_data,
        structlog.processors.StackInfoRenderer(),
    ]

    # Add format-specific processors
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Text/console format
        processors.extend(
            [
                structlog.processors.ExceptionRenderer(),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Optional logger name. If None, uses the calling module's name.

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context.

    Args:
        trace_id: Unique identifier for request tracing
    """
    trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """Clear trace ID from current context."""
    trace_id_var.set("")


__all__ = [
    "clear_trace_id",
    "get_logger",
    "set_trace_id",
    "setup_logging",
    "trace_id_var",
]
