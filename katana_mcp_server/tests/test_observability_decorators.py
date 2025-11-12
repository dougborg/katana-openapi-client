"""Tests for observability decorators (@observe_tool and @observe_service)."""

from unittest.mock import MagicMock, patch

import pytest
from katana_mcp.logging import observe_service, observe_tool, setup_logging


@pytest.fixture
def setup_test_logging():
    """Set up logging for tests."""
    setup_logging(log_level="DEBUG", log_format="json")


@pytest.mark.asyncio
async def test_observe_tool_success(setup_test_logging):
    """Test @observe_tool decorator logs successful tool execution."""

    @observe_tool
    async def sample_tool(param1: str, param2: int, ctx: str = "context") -> str:
        """Sample tool for testing."""
        return f"result: {param1}-{param2}"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute tool
        result = await sample_tool(param1="test", param2=42, ctx="ignored")

        # Verify result
        assert result == "result: test-42"

        # Verify logger calls
        assert mock_logger.info.call_count == 2

        # Check tool_invoked log
        first_call = mock_logger.info.call_args_list[0]
        assert first_call[0][0] == "tool_invoked"
        assert first_call[1]["tool_name"] == "sample_tool"
        assert first_call[1]["params"] == {"param1": "test", "param2": 42}

        # Check tool_completed log
        second_call = mock_logger.info.call_args_list[1]
        assert second_call[0][0] == "tool_completed"
        assert second_call[1]["tool_name"] == "sample_tool"
        assert second_call[1]["success"] is True
        assert "duration_ms" in second_call[1]
        assert second_call[1]["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_observe_tool_error(setup_test_logging):
    """Test @observe_tool decorator logs errors properly."""

    @observe_tool
    async def failing_tool(param: str, context: str = "ignored") -> str:
        """Tool that raises an exception."""
        raise ValueError("Test error")

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute tool and expect error
        with pytest.raises(ValueError, match="Test error"):
            await failing_tool(param="test", context="ctx")

        # Verify logger calls
        assert mock_logger.info.call_count == 1  # tool_invoked
        assert mock_logger.error.call_count == 1  # tool_failed

        # Check tool_invoked log
        invoked_call = mock_logger.info.call_args_list[0]
        assert invoked_call[0][0] == "tool_invoked"
        assert invoked_call[1]["tool_name"] == "failing_tool"
        assert invoked_call[1]["params"] == {"param": "test"}

        # Check tool_failed log
        error_call = mock_logger.error.call_args_list[0]
        assert error_call[0][0] == "tool_failed"
        assert error_call[1]["tool_name"] == "failing_tool"
        assert error_call[1]["success"] is False
        assert error_call[1]["error"] == "Test error"
        assert error_call[1]["error_type"] == "ValueError"
        assert "duration_ms" in error_call[1]


@pytest.mark.asyncio
async def test_observe_tool_filters_context_params(setup_test_logging):
    """Test @observe_tool decorator filters ctx/context parameters."""

    @observe_tool
    async def tool_with_context(
        data: str, ctx: str = "context1", context: str = "context2"
    ) -> str:
        """Tool with context parameters."""
        return f"data: {data}"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute tool
        await tool_with_context(data="test", ctx="ctx_value", context="context_value")

        # Check that ctx and context are filtered out
        invoked_call = mock_logger.info.call_args_list[0]
        params = invoked_call[1]["params"]
        assert params == {"data": "test"}
        assert "ctx" not in params
        assert "context" not in params


@pytest.mark.asyncio
async def test_observe_tool_preserves_function_metadata(setup_test_logging):
    """Test @observe_tool decorator preserves function metadata."""

    @observe_tool
    async def documented_tool(param: str) -> str:
        """This is a documented tool."""
        return param

    # Check that function metadata is preserved
    assert documented_tool.__name__ == "documented_tool"
    assert documented_tool.__doc__ == "This is a documented tool."


@pytest.mark.asyncio
async def test_observe_service_success(setup_test_logging):
    """Test @observe_service decorator logs successful service operations."""

    class TestService:
        @observe_service("fetch_data")
        async def fetch(self, item_id: int) -> str:
            """Fetch data by ID."""
            return f"data-{item_id}"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute service method
        service = TestService()
        result = await service.fetch(item_id=123)

        # Verify result
        assert result == "data-123"

        # Verify logger calls
        assert mock_logger.debug.call_count == 2

        # Check service_operation_started log
        first_call = mock_logger.debug.call_args_list[0]
        assert first_call[0][0] == "service_operation_started"
        assert first_call[1]["service"] == "TestService"
        assert first_call[1]["operation"] == "fetch_data"
        assert first_call[1]["params"] == {"item_id": 123}

        # Check service_operation_completed log
        second_call = mock_logger.debug.call_args_list[1]
        assert second_call[0][0] == "service_operation_completed"
        assert second_call[1]["service"] == "TestService"
        assert second_call[1]["operation"] == "fetch_data"
        assert second_call[1]["success"] is True
        assert "duration_ms" in second_call[1]


@pytest.mark.asyncio
async def test_observe_service_error(setup_test_logging):
    """Test @observe_service decorator logs errors properly."""

    class TestService:
        @observe_service("failing_operation")
        async def fail(self, message: str) -> str:
            """Operation that fails."""
            raise RuntimeError(message)

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute service method and expect error
        service = TestService()
        with pytest.raises(RuntimeError, match="Test failure"):
            await service.fail(message="Test failure")

        # Verify logger calls
        assert mock_logger.debug.call_count == 1  # service_operation_started
        assert mock_logger.error.call_count == 1  # service_operation_failed

        # Check service_operation_failed log
        error_call = mock_logger.error.call_args_list[0]
        assert error_call[0][0] == "service_operation_failed"
        assert error_call[1]["service"] == "TestService"
        assert error_call[1]["operation"] == "failing_operation"
        assert error_call[1]["success"] is False
        assert error_call[1]["error"] == "Test failure"
        assert error_call[1]["error_type"] == "RuntimeError"
        assert "duration_ms" in error_call[1]


@pytest.mark.asyncio
async def test_observe_service_preserves_function_metadata(setup_test_logging):
    """Test @observe_service decorator preserves function metadata."""

    class TestService:
        @observe_service("operation")
        async def method(self, param: str) -> str:
            """This is a documented method."""
            return param

    # Check that function metadata is preserved
    service = TestService()
    assert service.method.__name__ == "method"
    assert service.method.__doc__ == "This is a documented method."


@pytest.mark.asyncio
async def test_observe_tool_timing_accuracy(setup_test_logging):
    """Test that @observe_tool decorator measures time accurately."""
    import asyncio

    @observe_tool
    async def slow_tool(param: str) -> str:
        """Tool that takes time to execute."""
        await asyncio.sleep(0.1)  # Sleep for 100ms
        return param

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute tool
        await slow_tool(param="test")

        # Check that duration is roughly 100ms or more
        completed_call = mock_logger.info.call_args_list[1]
        duration_ms = completed_call[1]["duration_ms"]
        assert duration_ms >= 100  # Should be at least 100ms
        assert duration_ms < 200  # But not too much more (with some tolerance)


@pytest.mark.asyncio
async def test_observe_service_timing_accuracy(setup_test_logging):
    """Test that @observe_service decorator measures time accurately."""
    import asyncio

    class TestService:
        @observe_service("slow_operation")
        async def slow_method(self) -> str:
            """Method that takes time to execute."""
            await asyncio.sleep(0.05)  # Sleep for 50ms
            return "done"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute service method
        service = TestService()
        await service.slow_method()

        # Check that duration is roughly 50ms or more
        completed_call = mock_logger.debug.call_args_list[1]
        duration_ms = completed_call[1]["duration_ms"]
        assert duration_ms >= 50  # Should be at least 50ms
        assert duration_ms < 100  # But not too much more (with some tolerance)


@pytest.mark.asyncio
async def test_observe_tool_with_no_params(setup_test_logging):
    """Test @observe_tool decorator with a tool that has no parameters."""

    @observe_tool
    async def no_param_tool() -> str:
        """Tool with no parameters."""
        return "result"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute tool
        result = await no_param_tool()

        # Verify result
        assert result == "result"

        # Check that params is empty
        invoked_call = mock_logger.info.call_args_list[0]
        assert invoked_call[1]["params"] == {}


@pytest.mark.asyncio
async def test_observe_service_with_no_params(setup_test_logging):
    """Test @observe_service decorator with a method that has no parameters."""

    class TestService:
        @observe_service("no_param_operation")
        async def no_param_method(self) -> str:
            """Method with no parameters."""
            return "result"

    # Mock logger to capture calls
    with patch("katana_mcp.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Execute service method
        service = TestService()
        result = await service.no_param_method()

        # Verify result
        assert result == "result"

        # Check that params is empty
        started_call = mock_logger.debug.call_args_list[0]
        assert started_call[1]["params"] == {}
