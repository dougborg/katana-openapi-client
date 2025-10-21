from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.webhook_logs_export import WebhookLogsExport
from ...models.webhook_logs_export_request import WebhookLogsExportRequest


def _get_kwargs(
    *,
    body: WebhookLogsExportRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/webhook_logs_export",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | WebhookLogsExport | None:
    if response.status_code == 200:
        response_200 = WebhookLogsExport.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = DetailedErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DetailedErrorResponse | ErrorResponse | WebhookLogsExport]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookLogsExportRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | WebhookLogsExport]:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest): Request parameters for exporting webhook delivery logs
            for analysis and debugging Example: {'webhook_id': 1, 'start_date':
            '2024-01-10T00:00:00Z', 'end_date': '2024-01-15T23:59:59Z', 'status_filter': ['failure',
            'retry'], 'format': 'csv'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, WebhookLogsExport]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookLogsExportRequest,
) -> DetailedErrorResponse | ErrorResponse | WebhookLogsExport | None:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest): Request parameters for exporting webhook delivery logs
            for analysis and debugging Example: {'webhook_id': 1, 'start_date':
            '2024-01-10T00:00:00Z', 'end_date': '2024-01-15T23:59:59Z', 'status_filter': ['failure',
            'retry'], 'format': 'csv'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, WebhookLogsExport]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookLogsExportRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | WebhookLogsExport]:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest): Request parameters for exporting webhook delivery logs
            for analysis and debugging Example: {'webhook_id': 1, 'start_date':
            '2024-01-10T00:00:00Z', 'end_date': '2024-01-15T23:59:59Z', 'status_filter': ['failure',
            'retry'], 'format': 'csv'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, WebhookLogsExport]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookLogsExportRequest,
) -> DetailedErrorResponse | ErrorResponse | WebhookLogsExport | None:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest): Request parameters for exporting webhook delivery logs
            for analysis and debugging Example: {'webhook_id': 1, 'start_date':
            '2024-01-10T00:00:00Z', 'end_date': '2024-01-15T23:59:59Z', 'status_filter': ['failure',
            'retry'], 'format': 'csv'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, WebhookLogsExport]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
