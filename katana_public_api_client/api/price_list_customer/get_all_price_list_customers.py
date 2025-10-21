from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.price_list_customer_list_response import PriceListCustomerListResponse


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_ids: Unset | list[int] = UNSET,
    customer_ids: Unset | list[int] = UNSET,
    ids: Unset | list[int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_price_list_ids: Unset | list[int] = UNSET
    if not isinstance(price_list_ids, Unset):
        json_price_list_ids = price_list_ids

    params["price_list_ids"] = json_price_list_ids

    json_customer_ids: Unset | list[int] = UNSET
    if not isinstance(customer_ids, Unset):
        json_customer_ids = customer_ids

    params["customer_ids"] = json_customer_ids

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/price_list_customers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PriceListCustomerListResponse | None:
    if response.status_code == 200:
        response_200 = PriceListCustomerListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | PriceListCustomerListResponse]:
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
    price_list_ids: Unset | list[int] = UNSET,
    customer_ids: Unset | list[int] = UNSET,
    ids: Unset | list[int] = UNSET,
) -> Response[ErrorResponse | PriceListCustomerListResponse]:
    """List price list customers

     Returns a list of price list customers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_ids (Union[Unset, list[int]]):
        customer_ids (Union[Unset, list[int]]):
        ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, PriceListCustomerListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        price_list_ids=price_list_ids,
        customer_ids=customer_ids,
        ids=ids,
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
    price_list_ids: Unset | list[int] = UNSET,
    customer_ids: Unset | list[int] = UNSET,
    ids: Unset | list[int] = UNSET,
) -> ErrorResponse | PriceListCustomerListResponse | None:
    """List price list customers

     Returns a list of price list customers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_ids (Union[Unset, list[int]]):
        customer_ids (Union[Unset, list[int]]):
        ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, PriceListCustomerListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        price_list_ids=price_list_ids,
        customer_ids=customer_ids,
        ids=ids,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_ids: Unset | list[int] = UNSET,
    customer_ids: Unset | list[int] = UNSET,
    ids: Unset | list[int] = UNSET,
) -> Response[ErrorResponse | PriceListCustomerListResponse]:
    """List price list customers

     Returns a list of price list customers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_ids (Union[Unset, list[int]]):
        customer_ids (Union[Unset, list[int]]):
        ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, PriceListCustomerListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        price_list_ids=price_list_ids,
        customer_ids=customer_ids,
        ids=ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_ids: Unset | list[int] = UNSET,
    customer_ids: Unset | list[int] = UNSET,
    ids: Unset | list[int] = UNSET,
) -> ErrorResponse | PriceListCustomerListResponse | None:
    """List price list customers

     Returns a list of price list customers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_ids (Union[Unset, list[int]]):
        customer_ids (Union[Unset, list[int]]):
        ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, PriceListCustomerListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            price_list_ids=price_list_ids,
            customer_ids=customer_ids,
            ids=ids,
        )
    ).parsed
