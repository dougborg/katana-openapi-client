from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.price_list_row_list_response import PriceListRowListResponse


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    price_list_ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_price_list_ids: Unset | list[int] = UNSET
    if not isinstance(price_list_ids, Unset):
        json_price_list_ids = price_list_ids

    params["price_list_ids"] = json_price_list_ids

    json_variant_ids: Unset | list[int] = UNSET
    if not isinstance(variant_ids, Unset):
        json_variant_ids = variant_ids

    params["variant_ids"] = json_variant_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/price_list_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PriceListRowListResponse | None:
    if response.status_code == 200:
        response_200 = PriceListRowListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | PriceListRowListResponse]:
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
    ids: Unset | list[int] = UNSET,
    price_list_ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
) -> Response[ErrorResponse | PriceListRowListResponse]:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        price_list_ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, PriceListRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        price_list_ids=price_list_ids,
        variant_ids=variant_ids,
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
    ids: Unset | list[int] = UNSET,
    price_list_ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
) -> ErrorResponse | PriceListRowListResponse | None:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        price_list_ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, PriceListRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        price_list_ids=price_list_ids,
        variant_ids=variant_ids,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    price_list_ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
) -> Response[ErrorResponse | PriceListRowListResponse]:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        price_list_ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, PriceListRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        price_list_ids=price_list_ids,
        variant_ids=variant_ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    price_list_ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
) -> ErrorResponse | PriceListRowListResponse | None:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        price_list_ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, PriceListRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            price_list_ids=price_list_ids,
            variant_ids=variant_ids,
        )
    ).parsed
