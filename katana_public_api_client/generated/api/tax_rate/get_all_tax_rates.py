import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_tax_rates_response_401 import GetAllTaxRatesResponse401
from ...models.get_all_tax_rates_response_429 import GetAllTaxRatesResponse429
from ...models.get_all_tax_rates_response_500 import GetAllTaxRatesResponse500
from ...models.tax_rate_list_response import TaxRateListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    rate: Unset | float = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    is_default_sales: Unset | bool = UNSET,
    is_default_purchases: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["rate"] = rate

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["name"] = name

    params["is_default_sales"] = is_default_sales

    params["is_default_purchases"] = is_default_purchases

    params["limit"] = limit

    params["page"] = page

    json_created_at_min: Unset | str = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: Unset | str = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: Unset | str = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: Unset | str = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tax_rates",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
    | None
):
    if response.status_code == 200:
        response_200 = TaxRateListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllTaxRatesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllTaxRatesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllTaxRatesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
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
    rate: Unset | float = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    is_default_sales: Unset | bool = UNSET,
    is_default_purchases: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
]:
    """List all tax rates

     Returns a list of tax rate you've previously created.
        The tax rate are returned in sorted order, with the most recent tax rate appearing first.

    Args:
        rate (Union[Unset, float]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        is_default_sales (Union[Unset, bool]):
        is_default_purchases (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllTaxRatesResponse401, GetAllTaxRatesResponse429, GetAllTaxRatesResponse500, TaxRateListResponse]]
    """

    kwargs = _get_kwargs(
        rate=rate,
        ids=ids,
        name=name,
        is_default_sales=is_default_sales,
        is_default_purchases=is_default_purchases,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    rate: Unset | float = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    is_default_sales: Unset | bool = UNSET,
    is_default_purchases: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
    | None
):
    """List all tax rates

     Returns a list of tax rate you've previously created.
        The tax rate are returned in sorted order, with the most recent tax rate appearing first.

    Args:
        rate (Union[Unset, float]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        is_default_sales (Union[Unset, bool]):
        is_default_purchases (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllTaxRatesResponse401, GetAllTaxRatesResponse429, GetAllTaxRatesResponse500, TaxRateListResponse]
    """

    return sync_detailed(
        client=client,
        rate=rate,
        ids=ids,
        name=name,
        is_default_sales=is_default_sales,
        is_default_purchases=is_default_purchases,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    rate: Unset | float = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    is_default_sales: Unset | bool = UNSET,
    is_default_purchases: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
]:
    """List all tax rates

     Returns a list of tax rate you've previously created.
        The tax rate are returned in sorted order, with the most recent tax rate appearing first.

    Args:
        rate (Union[Unset, float]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        is_default_sales (Union[Unset, bool]):
        is_default_purchases (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllTaxRatesResponse401, GetAllTaxRatesResponse429, GetAllTaxRatesResponse500, TaxRateListResponse]]
    """

    kwargs = _get_kwargs(
        rate=rate,
        ids=ids,
        name=name,
        is_default_sales=is_default_sales,
        is_default_purchases=is_default_purchases,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    rate: Unset | float = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    is_default_sales: Unset | bool = UNSET,
    is_default_purchases: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllTaxRatesResponse401
    | GetAllTaxRatesResponse429
    | GetAllTaxRatesResponse500
    | TaxRateListResponse
    | None
):
    """List all tax rates

     Returns a list of tax rate you've previously created.
        The tax rate are returned in sorted order, with the most recent tax rate appearing first.

    Args:
        rate (Union[Unset, float]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        is_default_sales (Union[Unset, bool]):
        is_default_purchases (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllTaxRatesResponse401, GetAllTaxRatesResponse429, GetAllTaxRatesResponse500, TaxRateListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            rate=rate,
            ids=ids,
            name=name,
            is_default_sales=is_default_sales,
            is_default_purchases=is_default_purchases,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
