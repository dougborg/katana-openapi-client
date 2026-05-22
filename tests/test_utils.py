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

    def test_unwrap_returns_none_for_2xx_with_no_body(self):
        """A 2xx success with ``parsed=None`` is a legitimate 204 No Content
        response (most Katana POST/PATCH endpoints use this shape), not an
        error. Regression for #809: the previous behavior incorrectly raised
        ``APIError`` here, which broke every per-row apply on no-body
        endpoints — a 30-row BOM batch silently became a 1-row commit
        because the first 204 raised and fail-fast halted the rest.
        """
        response: Response[Any] = Response(
            status_code=HTTPStatus.NO_CONTENT,
            content=b"",
            headers={},
            parsed=None,
        )

        result = utils.unwrap(response)

        assert result is None

    def test_unwrap_returns_none_on_204_even_with_raise_on_error_false(self):
        """``raise_on_error=False`` is the legacy path; 2xx + parsed=None
        still returns None cleanly without consulting the error parser.
        """
        response: Response[Any] = Response(
            status_code=HTTPStatus.NO_CONTENT,
            content=b"",
            headers={},
            parsed=None,
        )

        result = utils.unwrap(response, raise_on_error=False)

        assert result is None

    def test_unwrap_raises_on_2xx_with_non_empty_body_and_parsed_none(self):
        """A 2xx with a non-empty body but ``parsed=None`` is the schema-drift
        signal: ``_parse_response`` didn't recognize the status (e.g. the
        server starts returning 201 with a body after an API change, but
        the spec still declares 204). Returning None there would silently
        drop the response and let downstream callers crash on ``.id``
        access; raising surfaces the drift instead.
        """
        body = b'{"id": 42, "name": "unexpected response shape"}'
        response: Response[Any] = Response(
            status_code=HTTPStatus(200),
            content=body,
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        assert exc_info.value.status_code == 200

    def test_unwrap_raises_on_non_2xx_with_parsed_none(self):
        """When the status is an error code and ``parsed`` is None
        (undocumented status, malformed body, etc.), the routing helper
        still raises ``APIError`` — this is the path the previous
        ``test_unwrap_with_none_parsed_raises_error`` was actually
        exercising for 4xx/5xx errors. Pin the behavior explicitly.
        """
        response: Response[Any] = Response(
            status_code=HTTPStatus(418),
            content=b"",
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        error = exc_info.value
        assert isinstance(error, utils.APIError)
        assert error.status_code == 418

    def test_unwrap_undocumented_status_surfaces_body(self):
        """Undocumented status codes (e.g. 412) parse the raw body and surface
        Katana's actual error name/message in the raised exception.

        412 has no dedicated APIError subclass (subclassing only kicks in for
        401/422/429/5xx), so the base ``APIError`` is raised — but with the
        body's name/message populated and ``error_response`` re-parsed from
        the nested-under-``"error"`` envelope.
        """
        body = (
            b'{"error":{"statusCode":412,"name":"PreconditionFailedError",'
            b'"message":"Cannot delete sales orders as sales orders have return orders."}}'
        )
        response: Response[Any] = Response(
            status_code=HTTPStatus(412),
            content=body,
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        error = exc_info.value
        assert type(error) is utils.APIError  # base class, not a subclass
        assert error.status_code == 412
        assert "PreconditionFailedError" in str(error)
        assert "Cannot delete sales orders" in str(error)
        assert isinstance(error.error_response, ErrorResponse)

    def test_unwrap_undocumented_status_routes_to_subclass(self):
        """When status code matches a known bucket (e.g. 503), the routing
        helper still picks the right APIError subclass even for undocumented
        statuses."""
        body = b'{"name":"ServiceUnavailable","message":"upstream down"}'
        response: Response[Any] = Response(
            status_code=HTTPStatus(503),
            content=body,
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.ServerError) as exc_info:
            utils.unwrap(response)

        assert "upstream down" in str(exc_info.value)

    def test_unwrap_undocumented_status_with_non_json_body(self):
        """When the body isn't JSON, fall back to a truncated snippet so the
        caller still sees what Katana sent."""
        response: Response[Any] = Response(
            status_code=HTTPStatus(502),
            content=b"<html><body>nginx 502 bad gateway</body></html>",
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.ServerError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert "UnexpectedResponse" in msg
        assert "nginx 502 bad gateway" in msg

    def test_unwrap_undocumented_status_with_long_body_truncates(self):
        """Long non-JSON bodies are truncated to keep the error readable."""
        response: Response[Any] = Response(
            status_code=HTTPStatus(418),
            content=b"x" * 1000,
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert "…" in msg  # truncation marker
        # 200-char limit on snippet + the "UnexpectedResponse: " prefix + "…"
        assert len(msg) < 300

    def test_unwrap_undocumented_status_with_invalid_utf8_body(self):
        """Bytes that aren't valid UTF-8 raise ``UnicodeDecodeError`` from
        ``json.loads`` (not ``JSONDecodeError``). The fallback must catch
        that and still produce an ``APIError`` with a body snippet."""
        # 0xc3 0x28 is a classic invalid UTF-8 continuation byte sequence
        response: Response[Any] = Response(
            status_code=HTTPStatus(502),
            content=b"\xc3\x28 bad gateway garbage",
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.ServerError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert "UnexpectedResponse" in msg
        # decode(errors="replace") substitutes U+FFFD for invalid bytes
        assert "bad gateway garbage" in msg

    def test_unwrap_undocumented_status_with_empty_json_object(self):
        """A JSON body of ``{}`` falls back to the empty-body placeholder
        rather than the misleading ``<no error message>`` default."""
        response: Response[Any] = Response(
            status_code=HTTPStatus(412),
            content=b"{}",
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert "<empty response body>" in msg
        assert "<no error message>" not in msg

    def test_unwrap_undocumented_status_with_unknown_dict_shape(self):
        """A JSON body that parses as a dict but doesn't carry name/message
        surfaces the JSON snippet instead of an opaque placeholder."""
        response: Response[Any] = Response(
            status_code=HTTPStatus(412),
            content=b'{"foo":"bar","baz":42}',
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert '"foo"' in msg
        assert '"bar"' in msg
        assert "<no error message>" not in msg

    def test_unwrap_undocumented_status_with_name_but_no_message(self):
        """When only ``name`` is present, ``message`` falls back to the body
        snippet so no detail is lost."""
        response: Response[Any] = Response(
            status_code=HTTPStatus(412),
            content=b'{"name":"PreconditionFailedError","reason":"check upstream"}',
            headers={},
            parsed=None,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        msg = str(exc_info.value)
        assert "PreconditionFailedError" in msg
        assert "check upstream" in msg
        assert "<no error message>" not in msg

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

        error = exc_info.value
        assert isinstance(error, utils.AuthenticationError)
        assert "Unauthorized: Invalid API key" in str(error)
        assert error.status_code == 401
        assert error.error_response == error_response

    def test_unwrap_422_raises_validation_error(self):
        """Test that 422 status raises ValidationError."""
        error_response = DetailedErrorResponse(
            status_code=422,
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

        error = exc_info.value
        assert isinstance(error, utils.ValidationError)
        assert "ValidationError: Invalid request data" in str(error)
        assert error.status_code == 422
        assert error.validation_errors == []

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

        error = exc_info.value
        assert isinstance(error, utils.RateLimitError)
        assert "TooManyRequestsError: Too Many Requests" in str(error)
        assert error.status_code == 429

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

        error = exc_info.value
        assert isinstance(error, utils.ServerError)
        assert "InternalServerError: Internal server error" in str(error)
        assert error.status_code == 500

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

    def test_unwrap_nested_error_reparses_into_error_response(self):
        """When the body uses the nested ``{"error": {...}}`` shape, the
        ``error_response`` attached to the raised exception must be re-parsed
        from the inner object so callers see the actual name/message/
        statusCode instead of the UNSET-everything outer envelope."""
        outer = ErrorResponse(name=UNSET, message=UNSET)
        outer.additional_properties = {
            "error": {
                "statusCode": 412,
                "name": "PreconditionFailedError",
                "message": "Cannot delete sales orders as sales orders have return orders.",
            }
        }
        response: Response[Any] = Response(
            status_code=HTTPStatus(412),
            content=b"{}",
            headers={},
            parsed=outer,
        )

        with pytest.raises(utils.APIError) as exc_info:
            utils.unwrap(response)

        err_resp = exc_info.value.error_response
        assert isinstance(err_resp, ErrorResponse)
        # Re-parsed from the inner dict, so these fields are now real
        assert err_resp.name == "PreconditionFailedError"
        assert "Cannot delete" in str(err_resp.message)


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


# ============================================================================
# Ajv-style ValidationErrorDetail formatter
#
# Each test mirrors a real Ajv ``ErrorObject`` wire shape:
# ``{path, code, message, info: {<keyword-specific>}}``. Tests go through
# ``unwrap()`` end-to-end (DetailedErrorResponse → discriminator → typed
# subtype → ValidationError.__str__) so we exercise the full path Katana's
# 422s actually take.
# ============================================================================


def _make_422_response(details: list[dict[str, Any]]) -> Response[Any]:
    """Build a ``Response`` carrying a Katana-shaped 422 with the given details."""
    body = {
        "error": {
            "statusCode": 422,
            "name": "UnprocessableEntityError",
            "message": "The request body is invalid. See error object `details` property for more info.",
            "code": "VALIDATION_FAILED",
            "details": details,
        }
    }
    return Response(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=b"",
        headers={},
        parsed=DetailedErrorResponse.from_dict(body),
    )


def _render(details: list[dict[str, Any]]) -> str:
    """Run details through ``unwrap()`` and return the formatted exception string."""
    with pytest.raises(utils.ValidationError) as exc_info:
        utils.unwrap(_make_422_response(details))
    return str(exc_info.value)


@pytest.mark.unit
class TestAjvStringKeywords:
    """``maxLength``, ``minLength``, ``pattern``, ``format``."""

    def test_max_length(self):
        rendered = _render(
            [
                {
                    "path": ".city",
                    "code": "maxLength",
                    "message": "should NOT be longer than 10 characters",
                    "info": {"limit": 10},
                }
            ]
        )
        assert "Field '.city' must not exceed 10 characters" in rendered

    def test_min_length(self):
        rendered = _render(
            [
                {
                    "path": ".sku",
                    "code": "minLength",
                    "message": "should NOT be shorter than 3 characters",
                    "info": {"limit": 3},
                }
            ]
        )
        assert "Field '.sku' must be at least 3 characters" in rendered

    def test_pattern(self):
        rendered = _render(
            [
                {
                    "path": ".phone",
                    "code": "pattern",
                    "message": "must match pattern",
                    "info": {"pattern": "^\\d+$"},
                }
            ]
        )
        assert "Field '.phone' must match pattern: ^\\d+$" in rendered

    def test_format(self):
        """Captured wire shape from ``tests/test_katana_client.py:218-223``."""
        rendered = _render(
            [
                {
                    "path": ".email",
                    "code": "format",
                    "message": 'should match format "email"',
                    "info": {"format": "email"},
                }
            ]
        )
        assert "Field '.email' must match format: email" in rendered


@pytest.mark.unit
class TestAjvNumericKeywords:
    """``minimum``, ``maximum``, ``exclusiveMinimum``, ``exclusiveMaximum``, ``multipleOf``."""

    def test_minimum(self):
        rendered = _render(
            [
                {
                    "path": ".price",
                    "code": "minimum",
                    "message": "must be >= 1",
                    "info": {"limit": 1, "comparison": ">="},
                }
            ]
        )
        assert "Field '.price' must be >= 1" in rendered

    def test_maximum(self):
        rendered = _render(
            [
                {
                    "path": ".price",
                    "code": "maximum",
                    "message": "must be <= 100",
                    "info": {"limit": 100, "comparison": "<="},
                }
            ]
        )
        assert "Field '.price' must be <= 100" in rendered

    def test_exclusive_minimum(self):
        rendered = _render(
            [
                {
                    "path": ".x",
                    "code": "exclusiveMinimum",
                    "message": "must be > 0",
                    "info": {"limit": 0, "comparison": ">"},
                }
            ]
        )
        assert "Field '.x' must be > 0" in rendered

    def test_exclusive_maximum(self):
        rendered = _render(
            [
                {
                    "path": ".x",
                    "code": "exclusiveMaximum",
                    "message": "must be < 1",
                    "info": {"limit": 1, "comparison": "<"},
                }
            ]
        )
        assert "Field '.x' must be < 1" in rendered

    def test_multiple_of(self):
        rendered = _render(
            [
                {
                    "path": ".n",
                    "code": "multipleOf",
                    "message": "must be a multiple of 2",
                    "info": {"multipleOf": 2},
                }
            ]
        )
        assert "Field '.n' must be a multiple of 2" in rendered


@pytest.mark.unit
class TestAjvArrayKeywords:
    """``minItems``, ``maxItems``, ``uniqueItems``."""

    def test_min_items(self):
        rendered = _render(
            [
                {
                    "path": ".tags",
                    "code": "minItems",
                    "message": ">= 1 items",
                    "info": {"limit": 1},
                }
            ]
        )
        assert "Field '.tags' must have at least 1 items" in rendered

    def test_max_items(self):
        rendered = _render(
            [
                {
                    "path": ".tags",
                    "code": "maxItems",
                    "message": "<= 5 items",
                    "info": {"limit": 5},
                }
            ]
        )
        assert "Field '.tags' must have at most 5 items" in rendered

    def test_unique_items(self):
        rendered = _render(
            [
                {
                    "path": ".tags",
                    "code": "uniqueItems",
                    "message": "duplicate items",
                    "info": {"i": 1, "j": 3},
                }
            ]
        )
        assert "Field '.tags' contains duplicate items at indices 1 and 3" in rendered


@pytest.mark.unit
class TestAjvObjectKeywords:
    """``required``, ``additionalProperties``, ``dependencies``."""

    def test_required(self):
        rendered = _render(
            [
                {
                    "path": "",
                    "code": "required",
                    "message": "missing property",
                    "info": {"missingProperty": "status"},
                }
            ]
        )
        assert "Missing required field: 'status'" in rendered

    def test_additional_properties(self):
        rendered = _render(
            [
                {
                    "path": "",
                    "code": "additionalProperties",
                    "message": "unexpected property",
                    "info": {"additionalProperty": "extra_field"},
                }
            ]
        )
        assert "has unexpected property: 'extra_field'" in rendered

    def test_dependencies(self):
        rendered = _render(
            [
                {
                    "path": "",
                    "code": "dependencies",
                    "message": "missing dependent",
                    "info": {
                        "property": "address",
                        "missingProperty": "city",
                        "deps": "city",
                        "depsCount": 1,
                    },
                }
            ]
        )
        assert (
            "has property 'address' but is missing dependent property 'city'"
            in rendered
        )


@pytest.mark.unit
class TestAjvTypeAndCompositionKeywords:
    """``type``, ``enum``, ``const``, ``oneOf``."""

    def test_type(self):
        rendered = _render(
            [
                {
                    "path": ".age",
                    "code": "type",
                    "message": "must be number",
                    "info": {"type": "number"},
                }
            ]
        )
        assert "Field '.age' must be of type: number" in rendered

    def test_enum(self):
        rendered = _render(
            [
                {
                    "path": ".status",
                    "code": "enum",
                    "message": "must be one of allowed values",
                    "info": {"allowedValues": ["NEW", "OPEN", "DONE"]},
                }
            ]
        )
        assert "Field '.status' must be one of:" in rendered
        assert "NEW" in rendered and "OPEN" in rendered and "DONE" in rendered

    def test_const(self):
        rendered = _render(
            [
                {
                    "path": ".version",
                    "code": "const",
                    "message": "must equal allowed value",
                    "info": {"allowedValue": 42},
                }
            ]
        )
        assert "Field '.version' must equal: 42" in rendered

    def test_one_of_zero_matches(self):
        rendered = _render(
            [
                {
                    "path": ".x",
                    "code": "oneOf",
                    "message": "no branch matched",
                    "info": {"passingSchemas": None},
                }
            ]
        )
        assert "Field '.x' did not match any allowed schema" in rendered

    def test_one_of_multiple_matches(self):
        rendered = _render(
            [
                {
                    "path": ".x",
                    "code": "oneOf",
                    "message": "multiple branches matched",
                    "info": {"passingSchemas": [0, 2]},
                }
            ]
        )
        assert "Field '.x' matched multiple allowed schemas" in rendered
        assert "[0, 2]" in rendered


@pytest.mark.unit
class TestAjvGenericFallback:
    """Codes the discriminator doesn't recognize fall back to GenericValidationError.

    The fallback formatter still surfaces ``path``, ``code``, ``message``, and
    any ``info`` captured in ``additional_properties`` — so future Ajv keywords
    (or custom user-defined keywords) don't go silent.
    """

    def test_unknown_keyword_with_info(self):
        rendered = _render(
            [
                {
                    "path": ".foo",
                    "code": "futureKeyword",
                    "message": "something invalid",
                    "info": {"someParam": "value"},
                }
            ]
        )
        assert "(futureKeyword)" in rendered
        assert "something invalid" in rendered
        assert "{'someParam': 'value'}" in rendered

    def test_unknown_keyword_without_info(self):
        rendered = _render(
            [
                {
                    "path": ".foo",
                    "code": "customKeyword",
                    "message": "rejected",
                }
            ]
        )
        assert "(customKeyword)" in rendered
        assert "rejected" in rendered

    def test_multiple_details_each_render(self):
        rendered = _render(
            [
                {
                    "path": ".city",
                    "code": "maxLength",
                    "message": "too long",
                    "info": {"limit": 10},
                },
                {
                    "path": "",
                    "code": "required",
                    "message": "missing",
                    "info": {"missingProperty": "country"},
                },
            ]
        )
        assert "Field '.city' must not exceed 10 characters" in rendered
        assert "Missing required field: 'country'" in rendered
