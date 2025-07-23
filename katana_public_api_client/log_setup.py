"""Logging setup utilities for the Katana API client.

This module provides logging configuration helpers for the enhanced Katana client.

"""

import logging
import logging.handlers
from pathlib import Path


class InfoToDebugFilter(logging.Filter):
    """Filter to convert INFO level logs to DEBUG level for specific loggers."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno == logging.INFO:
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"
        return True


def setup_logging(
    log_dir: str = "logs",
    log_file_prefix: str = "katana_client",
    log_level: int = logging.INFO,
    console_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Set up logging configuration for the Katana client.

    Args:
        log_dir: Directory to store log files
        log_file_prefix: Prefix for log file names
        log_level: Logging level for file handler
        console_level: Logging level for console handler
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance

    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger("katana_client")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler with rotation
    log_file = log_path / f"{log_file_prefix}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # Set up httpx logger with filter
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)
    httpx_logger.addFilter(InfoToDebugFilter())

    logger.info(
        f"Logging configured - File: {log_file}, Level: {logging.getLevelName(log_level)}"
    )

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to katana_client)

    Returns:
        Logger instance

    """
    return logging.getLogger(name or "katana_client")
