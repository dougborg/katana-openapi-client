from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_webhook_request import CreateWebhookRequest
from ...models.create_webhook_response_401 import CreateWebhookResponse401
from ...models.create_webhook_response_422 import CreateWebhookResponse422
from ...models.create_webhook_response_429 import CreateWebhookResponse429
from ...models.create_webhook_response_500 import CreateWebhookResponse500
from ...models.webhook import Webhook
from ...types import Response


def _get_kwargs(
    *,
    body: CreateWebhookRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/webhooks",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
    | None
):
    if response.status_code == 200:
        response_200 = Webhook.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateWebhookResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateWebhookResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateWebhookResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateWebhookResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
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
    body: CreateWebhookRequest,
) -> Response[
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
]:
    """Create a webhook

     Creates a new webhook object.

    Args:
        body (CreateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateWebhookResponse401, CreateWebhookResponse422, CreateWebhookResponse429, CreateWebhookResponse500, Webhook]]
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
    body: CreateWebhookRequest,
) -> (
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
    | None
):
    """Create a webhook

     Creates a new webhook object.

    Args:
        body (CreateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateWebhookResponse401, CreateWebhookResponse422, CreateWebhookResponse429, CreateWebhookResponse500, Webhook]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateWebhookRequest,
) -> Response[
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
]:
    """Create a webhook

     Creates a new webhook object.

    Args:
        body (CreateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateWebhookResponse401, CreateWebhookResponse422, CreateWebhookResponse429, CreateWebhookResponse500, Webhook]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateWebhookRequest,
) -> (
    CreateWebhookResponse401
    | CreateWebhookResponse422
    | CreateWebhookResponse429
    | CreateWebhookResponse500
    | Webhook
    | None
):
    """Create a webhook

     Creates a new webhook object.

    Args:
        body (CreateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateWebhookResponse401, CreateWebhookResponse422, CreateWebhookResponse429, CreateWebhookResponse500, Webhook]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
