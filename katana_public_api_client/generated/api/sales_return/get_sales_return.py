from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sales_return_response_401 import GetSalesReturnResponse401
from ...models.get_sales_return_response_404 import GetSalesReturnResponse404
from ...models.get_sales_return_response_429 import GetSalesReturnResponse429
from ...models.get_sales_return_response_500 import GetSalesReturnResponse500
from ...models.sales_return import SalesReturn
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/sales_returns/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
    | None
):
    if response.status_code == 200:
        response_200 = SalesReturn.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetSalesReturnResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = GetSalesReturnResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = GetSalesReturnResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetSalesReturnResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
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
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
]:
    """Retrieve a sales return

     Retrieves a sales return by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesReturnResponse401, GetSalesReturnResponse404, GetSalesReturnResponse429, GetSalesReturnResponse500, SalesReturn]]
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
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
    | None
):
    """Retrieve a sales return

     Retrieves a sales return by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesReturnResponse401, GetSalesReturnResponse404, GetSalesReturnResponse429, GetSalesReturnResponse500, SalesReturn]
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
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
]:
    """Retrieve a sales return

     Retrieves a sales return by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesReturnResponse401, GetSalesReturnResponse404, GetSalesReturnResponse429, GetSalesReturnResponse500, SalesReturn]]
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
    GetSalesReturnResponse401
    | GetSalesReturnResponse404
    | GetSalesReturnResponse429
    | GetSalesReturnResponse500
    | SalesReturn
    | None
):
    """Retrieve a sales return

     Retrieves a sales return by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesReturnResponse401, GetSalesReturnResponse404, GetSalesReturnResponse429, GetSalesReturnResponse500, SalesReturn]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
