from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_webhook_response_401 import DeleteWebhookResponse401
from ...models.delete_webhook_response_404 import DeleteWebhookResponse404
from ...models.delete_webhook_response_429 import DeleteWebhookResponse429
from ...models.delete_webhook_response_500 import DeleteWebhookResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/webhooks/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = DeleteWebhookResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteWebhookResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteWebhookResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteWebhookResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
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
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
]:
    """Delete webhook

     Deletes a single webhook by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteWebhookResponse401, DeleteWebhookResponse404, DeleteWebhookResponse429, DeleteWebhookResponse500]]
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
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
    | None
):
    """Delete webhook

     Deletes a single webhook by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteWebhookResponse401, DeleteWebhookResponse404, DeleteWebhookResponse429, DeleteWebhookResponse500]
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
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
]:
    """Delete webhook

     Deletes a single webhook by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteWebhookResponse401, DeleteWebhookResponse404, DeleteWebhookResponse429, DeleteWebhookResponse500]]
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
    Any
    | DeleteWebhookResponse401
    | DeleteWebhookResponse404
    | DeleteWebhookResponse429
    | DeleteWebhookResponse500
    | None
):
    """Delete webhook

     Deletes a single webhook by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteWebhookResponse401, DeleteWebhookResponse404, DeleteWebhookResponse429, DeleteWebhookResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
