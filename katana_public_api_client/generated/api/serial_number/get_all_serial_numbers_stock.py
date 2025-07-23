from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_serial_numbers_stock_response_401 import (
    GetAllSerialNumbersStockResponse401,
)
from ...models.get_all_serial_numbers_stock_response_429 import (
    GetAllSerialNumbersStockResponse429,
)
from ...models.get_all_serial_numbers_stock_response_500 import (
    GetAllSerialNumbersStockResponse500,
)
from ...models.get_all_serial_numbers_stock_status import GetAllSerialNumbersStockStatus
from ...models.serial_number_stock_list_response import SerialNumberStockListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSerialNumbersStockStatus = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["variant_id"] = variant_id

    params["location_id"] = location_id

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/serial_numbers_stock",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SerialNumberStockListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSerialNumbersStockResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSerialNumbersStockResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSerialNumbersStockResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSerialNumbersStockStatus = UNSET,
) -> Response[
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
]:
    """List serial number stock

     Returns a list of serial number stock.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSerialNumbersStockStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSerialNumbersStockResponse401, GetAllSerialNumbersStockResponse429, GetAllSerialNumbersStockResponse500, SerialNumberStockListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSerialNumbersStockStatus = UNSET,
) -> (
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
    | None
):
    """List serial number stock

     Returns a list of serial number stock.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSerialNumbersStockStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSerialNumbersStockResponse401, GetAllSerialNumbersStockResponse429, GetAllSerialNumbersStockResponse500, SerialNumberStockListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSerialNumbersStockStatus = UNSET,
) -> Response[
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
]:
    """List serial number stock

     Returns a list of serial number stock.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSerialNumbersStockStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSerialNumbersStockResponse401, GetAllSerialNumbersStockResponse429, GetAllSerialNumbersStockResponse500, SerialNumberStockListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSerialNumbersStockStatus = UNSET,
) -> (
    GetAllSerialNumbersStockResponse401
    | GetAllSerialNumbersStockResponse429
    | GetAllSerialNumbersStockResponse500
    | SerialNumberStockListResponse
    | None
):
    """List serial number stock

     Returns a list of serial number stock.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSerialNumbersStockStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSerialNumbersStockResponse401, GetAllSerialNumbersStockResponse429, GetAllSerialNumbersStockResponse500, SerialNumberStockListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            variant_id=variant_id,
            location_id=location_id,
            status=status,
        )
    ).parsed
