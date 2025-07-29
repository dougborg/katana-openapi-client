from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_serial_numbers_response_401 import GetAllSerialNumbersResponse401
from ...models.get_all_serial_numbers_response_429 import GetAllSerialNumbersResponse429
from ...models.get_all_serial_numbers_response_500 import GetAllSerialNumbersResponse500
from ...models.serial_number_stock_list_response import SerialNumberStockListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    serial_number: Unset | str = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["variant_id"] = variant_id

    params["location_id"] = location_id

    params["serial_number"] = serial_number

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/serial_numbers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
    | SerialNumberStockListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SerialNumberStockListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSerialNumbersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSerialNumbersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSerialNumbersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
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
    serial_number: Unset | str = UNSET,
) -> Response[
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
    | SerialNumberStockListResponse
]:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        serial_number (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSerialNumbersResponse401, GetAllSerialNumbersResponse429, GetAllSerialNumbersResponse500, SerialNumberStockListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        serial_number=serial_number,
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
    serial_number: Unset | str = UNSET,
) -> (
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
    | SerialNumberStockListResponse
    | None
):
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        serial_number (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSerialNumbersResponse401, GetAllSerialNumbersResponse429, GetAllSerialNumbersResponse500, SerialNumberStockListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        serial_number=serial_number,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    serial_number: Unset | str = UNSET,
) -> Response[
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
    | SerialNumberStockListResponse
]:
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        serial_number (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSerialNumbersResponse401, GetAllSerialNumbersResponse429, GetAllSerialNumbersResponse500, SerialNumberStockListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        location_id=location_id,
        serial_number=serial_number,
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
    serial_number: Unset | str = UNSET,
) -> (
    GetAllSerialNumbersResponse401
    | GetAllSerialNumbersResponse429
    | GetAllSerialNumbersResponse500
    | SerialNumberStockListResponse
    | None
):
    """List serial numbers

     Returns a list of serial numbers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        serial_number (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSerialNumbersResponse401, GetAllSerialNumbersResponse429, GetAllSerialNumbersResponse500, SerialNumberStockListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            variant_id=variant_id,
            location_id=location_id,
            serial_number=serial_number,
        )
    ).parsed
