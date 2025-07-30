from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_webhook_response_401 import GetWebhookResponse401
from ...models.get_webhook_response_429 import GetWebhookResponse429
from ...models.get_webhook_response_500 import GetWebhookResponse500
from ...models.webhook import Webhook
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/webhooks/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetWebhookResponse401
    | GetWebhookResponse429
    | GetWebhookResponse500
    | Webhook
    | None
):
    if response.status_code == 200:
        response_200 = Webhook.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetWebhookResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetWebhookResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetWebhookResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetWebhookResponse401 | GetWebhookResponse429 | GetWebhookResponse500 | Webhook
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetWebhookResponse401 | GetWebhookResponse429 | GetWebhookResponse500 | Webhook
]:
    """Retrieve a webhook

     Retrieves the details of an existing webhook based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetWebhookResponse401, GetWebhookResponse429, GetWebhookResponse500, Webhook]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetWebhookResponse401
    | GetWebhookResponse429
    | GetWebhookResponse500
    | Webhook
    | None
):
    """Retrieve a webhook

     Retrieves the details of an existing webhook based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetWebhookResponse401, GetWebhookResponse429, GetWebhookResponse500, Webhook]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetWebhookResponse401 | GetWebhookResponse429 | GetWebhookResponse500 | Webhook
]:
    """Retrieve a webhook

     Retrieves the details of an existing webhook based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetWebhookResponse401, GetWebhookResponse429, GetWebhookResponse500, Webhook]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetWebhookResponse401
    | GetWebhookResponse429
    | GetWebhookResponse500
    | Webhook
    | None
):
    """Retrieve a webhook

     Retrieves the details of an existing webhook based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetWebhookResponse401, GetWebhookResponse429, GetWebhookResponse500, Webhook]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
