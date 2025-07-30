from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.export_webhook_logs_response_401 import ExportWebhookLogsResponse401
from ...models.export_webhook_logs_response_422 import ExportWebhookLogsResponse422
from ...models.export_webhook_logs_response_429 import ExportWebhookLogsResponse429
from ...models.export_webhook_logs_response_500 import ExportWebhookLogsResponse500
from ...models.webhook_logs_export import WebhookLogsExport
from ...models.webhook_logs_export_request import WebhookLogsExportRequest
from ...types import Response


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
) -> (
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
    | None
):
    if response.status_code == 200:
        response_200 = WebhookLogsExport.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = ExportWebhookLogsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = ExportWebhookLogsResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = ExportWebhookLogsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = ExportWebhookLogsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
]:
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
) -> Response[
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
]:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ExportWebhookLogsResponse401, ExportWebhookLogsResponse422, ExportWebhookLogsResponse429, ExportWebhookLogsResponse500, WebhookLogsExport]]
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
) -> (
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
    | None
):
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ExportWebhookLogsResponse401, ExportWebhookLogsResponse422, ExportWebhookLogsResponse429, ExportWebhookLogsResponse500, WebhookLogsExport]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: WebhookLogsExportRequest,
) -> Response[
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
]:
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ExportWebhookLogsResponse401, ExportWebhookLogsResponse422, ExportWebhookLogsResponse429, ExportWebhookLogsResponse500, WebhookLogsExport]]
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
) -> (
    ExportWebhookLogsResponse401
    | ExportWebhookLogsResponse422
    | ExportWebhookLogsResponse429
    | ExportWebhookLogsResponse500
    | WebhookLogsExport
    | None
):
    """Export webhook logs

     Use the endpoint to export your webhook logs and troubleshoot any issues.
          Webhook logs are filtered by the provided parameters and exported into a CSV file.
          The response contains an URL to the CSV file.

    Args:
        body (WebhookLogsExportRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ExportWebhookLogsResponse401, ExportWebhookLogsResponse422, ExportWebhookLogsResponse429, ExportWebhookLogsResponse500, WebhookLogsExport]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
