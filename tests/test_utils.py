"""Tests for utility functions in katana_public_api_client.utils."""

from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import pytest

from katana_public_api_client import utils
from katana_public_api_client.client_types import UNSET, Response
from katana_public_api_client.models.detailed_error_response import (
    DetailedErrorResponse,
)
from katana_public_api_client.models.error_response import ErrorResponse
from katana_public_api_client.models.webhook import Webhook
from katana_public_api_client.models.webhook_list_response import WebhookListResponse


@pytest.mark.unit
class TestUnwrap:
    """Test the unwrap() function."""

    def test_unwrap_successful_response(self):
        """Test unwrapping a successful response returns parsed data."""
        webhook_data = WebhookListResponse(data=[])
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_data,
        )

        result = utils.unwrap(response)

        assert result == webhook_data
        assert isinstance(result, WebhookListResponse)

    def test_unwrap_with_none_parsed_raises_error(self):
        """Test that unwrap raises APIError when parsed is None."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        assert "No parsed response data" in str(exc_info.value)
        assert exc_info.value.status_code == 200

    def test_unwrap_with_none_parsed_returns_none_when_not_raising(self):
        """Test that unwrap returns None when parsed is None and raise_on_error=False."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=None,
        )

        result = utils.unwrap(response, raise_on_error=False)

        assert result is None

    def test_unwrap_401_raises_authentication_error(self):
        """Test that 401 status raises AuthenticationError."""
        error_response = ErrorResponse(
            name="Unauthorized",
            message="Invalid API key",
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.UNAUTHORIZED,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.AuthenticationError) as exc_info:
            utils.unwrap(response)

        assert "Unauthorized: Invalid API key" in str(exc_info.value)
        assert exc_info.value.status_code == 401
        assert exc_info.value.error_response == error_response

    def test_unwrap_422_raises_validation_error(self):
        """Test that 422 status raises ValidationError."""
        error_response = DetailedErrorResponse(
            name="ValidationError",
            message="Invalid request data",
            details=[],
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.ValidationError) as exc_info:
            utils.unwrap(response)

        assert "ValidationError: Invalid request data" in str(exc_info.value)
        assert exc_info.value.status_code == 422
        assert exc_info.value.validation_errors == []

    def test_unwrap_with_raise_on_error_false_returns_none(self):
        """Test that unwrap with raise_on_error=False returns None on error."""
        error_response = ErrorResponse(
            name="BadRequest",
            message="Invalid parameters",
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        result = utils.unwrap(response, raise_on_error=False)

        assert result is None

    def test_unwrap_type_safety_with_raise_on_error_true(self):
        """Test that unwrap with raise_on_error=True has correct type inference.

        This test demonstrates that when raise_on_error=True, mypy infers
        the return type as T (never None), eliminating the need for cast().
        """
        webhook_data = WebhookListResponse(data=[])
        response: Response[WebhookListResponse] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_data,
        )

        # With raise_on_error=True, mypy infers: WebhookListResponse (no cast needed!)
        result = utils.unwrap(response, raise_on_error=True)

        # This should work without any type: ignore or cast() because
        # mypy knows result is WebhookListResponse, never None
        assert isinstance(result, WebhookListResponse)
        assert result.data == []

    def test_unwrap_type_safety_with_raise_on_error_false(self):
        """Test that unwrap with raise_on_error=False has correct type inference.

        This test demonstrates that when raise_on_error=False, mypy infers
        the return type as T | None, requiring proper None checks.
        """
        webhook_data = WebhookListResponse(data=[])
        response: Response[WebhookListResponse] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_data,
        )

        # With raise_on_error=False, mypy infers: WebhookListResponse | None
        result = utils.unwrap(response, raise_on_error=False)

        # mypy will require None check here
        if result is not None:
            assert isinstance(result, WebhookListResponse)
            assert result.data == []

    def test_unwrap_429_raises_rate_limit_error(self):
        """Test that 429 status raises RateLimitError."""
        error_response = ErrorResponse(
            name="TooManyRequestsError",
            message="Too Many Requests",
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.RateLimitError) as exc_info:
            utils.unwrap(response)

        assert "TooManyRequestsError: Too Many Requests" in str(exc_info.value)
        assert exc_info.value.status_code == 429

    def test_unwrap_500_raises_server_error(self):
        """Test that 500 status raises ServerError."""
        error_response = ErrorResponse(
            name="InternalServerError",
            message="Internal server error",
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.ServerError) as exc_info:
            utils.unwrap(response)

        assert "InternalServerError: Internal server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_unwrap_error_with_raise_on_error_false_returns_none(self):
        """Test that errors return None when raise_on_error=False."""
        error_response = ErrorResponse(
            name="Error",
            message="Some error",
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        result = utils.unwrap(response, raise_on_error=False)

        assert result is None

    def test_unwrap_handles_unset_error_fields(self):
        """Test that unwrap handles Unset error name/message fields."""
        error_response = ErrorResponse(
            name=UNSET,
            message=UNSET,
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        assert "Unknown: No error message provided" in str(exc_info.value)

    def test_unwrap_handles_nested_error_format(self):
        """Test that unwrap extracts error from nested additional_properties."""
        error_response = ErrorResponse(
            name=UNSET,
            message=UNSET,
        )
        error_response.additional_properties = {
            "error": {
                "statusCode": 400,
                "name": "BadRequestError",
                "message": "Invalid parameter",
            }
        }
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        assert "BadRequestError: Invalid parameter" in str(exc_info.value)


@pytest.mark.unit
class TestUnwrapData:
    """Test the unwrap_data() function."""

    def test_unwrap_data_from_list_response(self):
        """Test unwrapping data from a list response."""
        webhook1 = Webhook(id=1, url="https://example.com", enabled=True, token="abc")
        webhook2 = Webhook(id=2, url="https://example.com", enabled=False, token="def")
        webhook_list = WebhookListResponse(data=[webhook1, webhook2])
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )

        result = utils.unwrap_data(response)
        assert result is not None

        assert len(result) == 2
        assert result[0] == webhook1
        assert result[1] == webhook2

    def test_unwrap_data_from_single_object_returns_list(self):
        """Test that unwrap_data returns single object as a list."""
        webhook = Webhook(id=1, url="https://example.com", enabled=True, token="abc")
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook,
        )

        result = utils.unwrap_data(response)
        assert result is not None

        assert len(result) == 1
        assert result[0] == webhook

    def test_unwrap_data_with_unset_data_returns_empty_list(self):
        """Test that unwrap_data returns empty list when data is Unset."""
        webhook_list = WebhookListResponse(data=UNSET)
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )

        result = utils.unwrap_data(response)

        assert result == []

    def test_unwrap_data_with_default(self):
        """Test that unwrap_data returns default when data is Unset."""
        webhook_list = WebhookListResponse(data=UNSET)
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )
        default: list[Webhook] = [
            Webhook(id=99, url="default", enabled=True, token="xyz")
        ]

        result = utils.unwrap_data(response, default=default)

        assert result == default

    def test_unwrap_data_with_error_and_raise_on_error_false(self):
        """Test that unwrap_data returns default on error when raise_on_error=False."""
        error_response = ErrorResponse(name="Error", message="Test error")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )
        default: list[Any] = []

        result = utils.unwrap_data(response, raise_on_error=False, default=default)

        assert result == default

    def test_unwrap_data_with_error_raises_by_default(self):
        """Test that unwrap_data raises on error by default."""
        error_response = ErrorResponse(name="Error", message="Test error")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        with pytest.raises(utils.APIError):
            utils.unwrap_data(response)


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions like is_success, is_error, get_error_message."""

    def test_is_success_with_200(self):
        """Test is_success returns True for 2xx status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_success(response) is True

    def test_is_success_with_201(self):
        """Test is_success returns True for 201 status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.CREATED,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_success(response) is True

    def test_is_success_with_400(self):
        """Test is_success returns False for 4xx status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_success(response) is False

    def test_is_error_with_400(self):
        """Test is_error returns True for 4xx status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_error(response) is True

    def test_is_error_with_500(self):
        """Test is_error returns True for 5xx status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_error(response) is True

    def test_is_error_with_200(self):
        """Test is_error returns False for 2xx status."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=None,
        )

        assert utils.is_error(response) is False

    def test_get_error_message_from_error_response(self):
        """Test extracting error message from ErrorResponse."""
        error_response = ErrorResponse(name="Error", message="Something went wrong")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        message = utils.get_error_message(response)

        assert message == "Something went wrong"

    def test_get_error_message_from_nested_error(self):
        """Test extracting error message from nested error format."""
        error_response = ErrorResponse(
            name=UNSET,
            message=UNSET,
        )
        error_response.additional_properties = {
            "error": {"statusCode": 400, "message": "Nested error message"}
        }
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        message = utils.get_error_message(response)

        assert message == "Nested error message"

    def test_get_error_message_returns_none_for_non_error(self):
        """Test get_error_message returns None for non-error response."""
        webhook_list = WebhookListResponse(data=[])
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )

        message = utils.get_error_message(response)

        assert message is None

    def test_get_error_message_returns_none_when_parsed_is_none(self):
        """Test get_error_message returns None when parsed is None."""
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=None,
        )

        message = utils.get_error_message(response)

        assert message is None


@pytest.mark.unit
class TestHandleResponse:
    """Test the handle_response() function."""

    def test_handle_response_calls_on_success(self):
        """Test that on_success callback is called for successful response."""
        webhook_list = WebhookListResponse(data=[])
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )

        on_success = MagicMock(return_value="success_result")
        result = utils.handle_response(response, on_success=on_success)

        on_success.assert_called_once_with(webhook_list)
        assert result == "success_result"

    def test_handle_response_calls_on_error(self):
        """Test that on_error callback is called for error response."""
        error_response = ErrorResponse(name="Error", message="Test error")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        on_error = MagicMock(return_value="error_result")
        result = utils.handle_response(response, on_error=on_error)

        on_error.assert_called_once()
        assert isinstance(on_error.call_args[0][0], utils.APIError)
        assert result == "error_result"

    def test_handle_response_raises_when_raise_on_error_true(self):
        """Test that errors are raised when raise_on_error=True."""
        error_response = ErrorResponse(name="Error", message="Test error")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        on_error = MagicMock()

        with pytest.raises(utils.APIError):
            utils.handle_response(response, on_error=on_error, raise_on_error=True)

        # on_error should not be called when raise_on_error=True
        on_error.assert_not_called()

    def test_handle_response_returns_data_when_no_callbacks(self):
        """Test that response data is returned when no callbacks provided."""
        webhook_list = WebhookListResponse(data=[])
        response: Response[Any] = Response(
            status_code=HTTPStatus.OK,
            content=b"{}",
            headers={},
            parsed=webhook_list,
        )

        result = utils.handle_response(response)

        assert result == webhook_list

    def test_handle_response_returns_none_on_error_without_callback(self):
        """Test that None is returned on error when no on_error callback."""
        error_response = ErrorResponse(name="Error", message="Test error")
        response: Response[Any] = Response(
            status_code=HTTPStatus.BAD_REQUEST,
            content=b"{}",
            headers={},
            parsed=error_response,
        )

        result = utils.handle_response(response)

        assert result is None
