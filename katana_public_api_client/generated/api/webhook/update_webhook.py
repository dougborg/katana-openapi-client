from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_webhook_request import UpdateWebhookRequest
from ...models.update_webhook_response_401 import UpdateWebhookResponse401
from ...models.update_webhook_response_422 import UpdateWebhookResponse422
from ...models.update_webhook_response_429 import UpdateWebhookResponse429
from ...models.update_webhook_response_500 import UpdateWebhookResponse500
from ...models.webhook import Webhook
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateWebhookRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/webhooks/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
    | None
):
    if response.status_code == 200:
        response_200 = Webhook.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateWebhookResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = UpdateWebhookResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdateWebhookResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateWebhookResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
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
    body: UpdateWebhookRequest,
) -> Response[
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
]:
    """Update a webhook

     Updates the specified webhook by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[UpdateWebhookResponse401, UpdateWebhookResponse422, UpdateWebhookResponse429, UpdateWebhookResponse500, Webhook]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateWebhookRequest,
) -> (
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
    | None
):
    """Update a webhook

     Updates the specified webhook by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[UpdateWebhookResponse401, UpdateWebhookResponse422, UpdateWebhookResponse429, UpdateWebhookResponse500, Webhook]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateWebhookRequest,
) -> Response[
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
]:
    """Update a webhook

     Updates the specified webhook by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[UpdateWebhookResponse401, UpdateWebhookResponse422, UpdateWebhookResponse429, UpdateWebhookResponse500, Webhook]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateWebhookRequest,
) -> (
    UpdateWebhookResponse401
    | UpdateWebhookResponse422
    | UpdateWebhookResponse429
    | UpdateWebhookResponse500
    | Webhook
    | None
):
    """Update a webhook

     Updates the specified webhook by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateWebhookRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[UpdateWebhookResponse401, UpdateWebhookResponse422, UpdateWebhookResponse429, UpdateWebhookResponse500, Webhook]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
