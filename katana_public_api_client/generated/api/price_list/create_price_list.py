from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_price_list_request import CreatePriceListRequest
from ...models.create_price_list_response_400 import CreatePriceListResponse400
from ...models.create_price_list_response_401 import CreatePriceListResponse401
from ...models.create_price_list_response_422 import CreatePriceListResponse422
from ...models.create_price_list_response_429 import CreatePriceListResponse429
from ...models.create_price_list_response_500 import CreatePriceListResponse500
from ...models.price_list import PriceList
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePriceListRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/price_lists",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
    | None
):
    if response.status_code == 201:
        response_201 = PriceList.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CreatePriceListResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = CreatePriceListResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePriceListResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePriceListResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePriceListResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
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
    body: CreatePriceListRequest,
) -> Response[
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
]:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListResponse400, CreatePriceListResponse401, CreatePriceListResponse422, CreatePriceListResponse429, CreatePriceListResponse500, PriceList]]
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
    body: CreatePriceListRequest,
) -> (
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
    | None
):
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListResponse400, CreatePriceListResponse401, CreatePriceListResponse422, CreatePriceListResponse429, CreatePriceListResponse500, PriceList]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRequest,
) -> Response[
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
]:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListResponse400, CreatePriceListResponse401, CreatePriceListResponse422, CreatePriceListResponse429, CreatePriceListResponse500, PriceList]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRequest,
) -> (
    CreatePriceListResponse400
    | CreatePriceListResponse401
    | CreatePriceListResponse422
    | CreatePriceListResponse429
    | CreatePriceListResponse500
    | PriceList
    | None
):
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListResponse400, CreatePriceListResponse401, CreatePriceListResponse422, CreatePriceListResponse429, CreatePriceListResponse500, PriceList]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
