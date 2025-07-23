from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_webhooks_response_401 import GetAllWebhooksResponse401
from ...models.get_all_webhooks_response_429 import GetAllWebhooksResponse429
from ...models.get_all_webhooks_response_500 import GetAllWebhooksResponse500
from ...models.webhook_list_response import WebhookListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    url_query: Unset | str = UNSET,
    enabled: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["url"] = url_query

    params["enabled"] = enabled

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/webhooks",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
    | None
):
    if response.status_code == 200:
        response_200 = WebhookListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllWebhooksResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllWebhooksResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllWebhooksResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
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
    ids: Unset | list[int] = UNSET,
    url_query: Unset | str = UNSET,
    enabled: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
]:
    """List all webhooks

     Returns a list of webhooks you've previously created. The entries are returned in a sorted order,
        with the most recent ones appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        url_query (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllWebhooksResponse401, GetAllWebhooksResponse429, GetAllWebhooksResponse500, WebhookListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        url_query=url_query,
        enabled=enabled,
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    url_query: Unset | str = UNSET,
    enabled: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
    | None
):
    """List all webhooks

     Returns a list of webhooks you've previously created. The entries are returned in a sorted order,
        with the most recent ones appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        url_query (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllWebhooksResponse401, GetAllWebhooksResponse429, GetAllWebhooksResponse500, WebhookListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        url_query=url_query,
        enabled=enabled,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    url_query: Unset | str = UNSET,
    enabled: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
]:
    """List all webhooks

     Returns a list of webhooks you've previously created. The entries are returned in a sorted order,
        with the most recent ones appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        url_query (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllWebhooksResponse401, GetAllWebhooksResponse429, GetAllWebhooksResponse500, WebhookListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        url_query=url_query,
        enabled=enabled,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    url_query: Unset | str = UNSET,
    enabled: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllWebhooksResponse401
    | GetAllWebhooksResponse429
    | GetAllWebhooksResponse500
    | WebhookListResponse
    | None
):
    """List all webhooks

     Returns a list of webhooks you've previously created. The entries are returned in a sorted order,
        with the most recent ones appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        url_query (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllWebhooksResponse401, GetAllWebhooksResponse429, GetAllWebhooksResponse500, WebhookListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            url_query=url_query,
            enabled=enabled,
            limit=limit,
            page=page,
        )
    ).parsed
