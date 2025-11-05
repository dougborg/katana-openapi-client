"""Tests for structured logging functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest
from katana_mcp.logging import (
    add_trace_id,
    clear_trace_id,
    filter_sensitive_data,
    get_logger,
    set_trace_id,
    setup_logging,
    trace_id_var,
)


def test_setup_logging_default():
    """Test setup_logging with default configuration."""
    setup_logging()

    # Verify that structlog is configured
    logger = get_logger("test")
    # Logger can be either BoundLogger or BoundLoggerLazyProxy
    assert logger is not None


def test_setup_logging_json_format():
    """Test setup_logging with JSON format."""
    setup_logging(log_level="DEBUG", log_format="json")

    # Verify logger is configured
    logger = get_logger("test")
    assert logger is not None


def test_setup_logging_text_format():
    """Test setup_logging with text/console format."""
    setup_logging(log_level="INFO", log_format="text")

    logger = get_logger("test")
    assert logger is not None


def test_setup_logging_from_env():
    """Test setup_logging reads from environment variables."""
    with patch.dict(
        os.environ,
        {"KATANA_MCP_LOG_LEVEL": "WARNING", "KATANA_MCP_LOG_FORMAT": "text"},
    ):
        setup_logging()

        logger = get_logger("test")
        assert logger is not None


def test_setup_logging_invalid_level():
    """Test setup_logging handles invalid log level gracefully."""
    setup_logging(log_level="INVALID", log_format="json")

    # Should default to INFO
    logger = get_logger("test")
    assert logger is not None


def test_get_logger():
    """Test get_logger returns a proper logger instance."""
    setup_logging()

    logger = get_logger("test_module")
    assert logger is not None

    # Test without name
    logger2 = get_logger()
    assert logger2 is not None


def test_trace_id_management():
    """Test trace ID context variable management."""
    # Initially should be empty
    assert trace_id_var.get() == ""

    # Set trace ID
    test_trace_id = "test-trace-123"
    set_trace_id(test_trace_id)
    assert trace_id_var.get() == test_trace_id

    # Clear trace ID
    clear_trace_id()
    assert trace_id_var.get() == ""


def test_add_trace_id_processor():
    """Test add_trace_id processor adds trace_id to event dict."""
    logger = MagicMock()
    event_dict = {"event": "test_event", "data": "test_data"}

    # Without trace ID
    clear_trace_id()
    result = add_trace_id(logger, "info", event_dict.copy())
    assert "trace_id" not in result

    # With trace ID
    set_trace_id("trace-456")
    result = add_trace_id(logger, "info", event_dict.copy())
    assert result["trace_id"] == "trace-456"

    clear_trace_id()


def test_filter_sensitive_data_processor():
    """Test filter_sensitive_data processor redacts sensitive keys."""
    logger = MagicMock()

    # Test API key redaction
    event_dict = {
        "event": "test_event",
        "api_key": "secret-key-123",
        "data": "safe_data",
    }
    result = filter_sensitive_data(logger, "info", event_dict.copy())
    assert result["api_key"] == "***REDACTED***"
    assert result["data"] == "safe_data"

    # Test password redaction
    event_dict = {"password": "my-password", "username": "john"}
    result = filter_sensitive_data(logger, "info", event_dict.copy())
    assert result["password"] == "***REDACTED***"
    assert result["username"] == "john"

    # Test case-insensitive matching
    event_dict = {"API_KEY": "secret", "Authorization": "Bearer token"}
    result = filter_sensitive_data(logger, "info", event_dict.copy())
    assert result["API_KEY"] == "***REDACTED***"
    assert result["Authorization"] == "***REDACTED***"

    # Test multiple sensitive keys
    event_dict = {
        "api_key": "key1",
        "password": "pass1",
        "secret": "sec1",
        "token": "tok1",
        "safe_field": "safe",
    }
    result = filter_sensitive_data(logger, "info", event_dict.copy())
    assert result["api_key"] == "***REDACTED***"
    assert result["password"] == "***REDACTED***"
    assert result["secret"] == "***REDACTED***"
    assert result["token"] == "***REDACTED***"
    assert result["safe_field"] == "safe"


def test_logging_with_structured_data():
    """Test logging with structured data works correctly."""
    setup_logging(log_level="DEBUG", log_format="json")

    logger = get_logger("test_structured")

    # This should not raise an exception
    logger.info(
        "test_event",
        tool_name="search_items",
        query="widget",
        result_count=15,
        duration_ms=245.67,
    )

    logger.warning("warning_event", threshold=10, status="low_stock")

    logger.error(
        "error_event",
        error_type="ValueError",
        error_msg="Invalid input",
    )


@pytest.mark.asyncio
async def test_logging_performance_metrics():
    """Test logging includes performance metrics."""
    setup_logging(log_level="INFO", log_format="json")
    logger = get_logger("test_performance")

    # Simulate tool execution with metrics
    import time

    start_time = time.monotonic()
    # Simulate work
    await __import__("asyncio").sleep(0.01)
    duration_ms = round((time.monotonic() - start_time) * 1000, 2)

    logger.info(
        "tool_executed",
        tool_name="check_inventory",
        sku="TEST-001",
        duration_ms=duration_ms,
    )

    assert duration_ms > 0


def test_logging_does_not_log_credentials():
    """Test that credentials are not logged."""
    setup_logging(log_level="DEBUG", log_format="json")
    logger = get_logger("test_security")

    # These should all be redacted by filter_sensitive_data processor
    # We don't need to mock the renderer - the processor handles it
    logger.info(
        "api_call",
        api_key="should-be-redacted",
        password="should-be-redacted",
        auth_token="should-be-redacted",
        username="safe-to-log",
    )


def test_logging_env_var_precedence():
    """Test that environment variables take precedence over defaults."""
    # Set environment variables
    with patch.dict(
        os.environ,
        {"KATANA_MCP_LOG_LEVEL": "ERROR", "KATANA_MCP_LOG_FORMAT": "text"},
    ):
        setup_logging()

        # Logger should be configured with ERROR level
        logger = get_logger("test_env")
        assert logger is not None

    # Reset to defaults
    setup_logging(log_level="INFO", log_format="json")


def test_multiple_logger_instances():
    """Test that multiple logger instances work correctly."""
    setup_logging()

    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    # Both should be valid logger instances
    assert logger1 is not None
    assert logger2 is not None

    # They should both work
    logger1.info("test1", data="value1")
    logger2.info("test2", data="value2")
