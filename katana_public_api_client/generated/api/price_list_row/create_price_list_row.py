from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_price_list_row_request import CreatePriceListRowRequest
from ...models.create_price_list_row_response_400 import CreatePriceListRowResponse400
from ...models.create_price_list_row_response_401 import CreatePriceListRowResponse401
from ...models.create_price_list_row_response_422 import CreatePriceListRowResponse422
from ...models.create_price_list_row_response_429 import CreatePriceListRowResponse429
from ...models.create_price_list_row_response_500 import CreatePriceListRowResponse500
from ...models.price_list_row import PriceListRow
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePriceListRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/price_list_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
    | None
):
    if response.status_code == 201:
        response_201 = PriceListRow.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CreatePriceListRowResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = CreatePriceListRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePriceListRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePriceListRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePriceListRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
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
    body: CreatePriceListRowRequest,
) -> Response[
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
]:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListRowResponse400, CreatePriceListRowResponse401, CreatePriceListRowResponse422, CreatePriceListRowResponse429, CreatePriceListRowResponse500, PriceListRow]]
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
    body: CreatePriceListRowRequest,
) -> (
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
    | None
):
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListRowResponse400, CreatePriceListRowResponse401, CreatePriceListRowResponse422, CreatePriceListRowResponse429, CreatePriceListRowResponse500, PriceListRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRowRequest,
) -> Response[
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
]:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListRowResponse400, CreatePriceListRowResponse401, CreatePriceListRowResponse422, CreatePriceListRowResponse429, CreatePriceListRowResponse500, PriceListRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRowRequest,
) -> (
    CreatePriceListRowResponse400
    | CreatePriceListRowResponse401
    | CreatePriceListRowResponse422
    | CreatePriceListRowResponse429
    | CreatePriceListRowResponse500
    | PriceListRow
    | None
):
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListRowResponse400, CreatePriceListRowResponse401, CreatePriceListRowResponse422, CreatePriceListRowResponse429, CreatePriceListRowResponse500, PriceListRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
