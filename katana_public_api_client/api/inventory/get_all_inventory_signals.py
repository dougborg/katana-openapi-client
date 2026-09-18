from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_inventory_signals_stock_risk import (
    GetAllInventorySignalsStockRisk,
)
from ...models.inventory_signal_list_response import InventorySignalListResponse


def _get_kwargs(
    *,
    variant_id: list[int] | Unset = UNSET,
    stock_risk: GetAllInventorySignalsStockRisk | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_variant_id: list[int] | Unset = UNSET
    if not isinstance(variant_id, Unset):
        json_variant_id = variant_id

    params["variant_id"] = json_variant_id

    json_stock_risk: int | Unset = UNSET
    if not isinstance(stock_risk, Unset):
        json_stock_risk = stock_risk.value

    params["stock_risk"] = json_stock_risk

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/inventory_signals",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | InventorySignalListResponse | None:
    if response.status_code == 200:
        response_200 = InventorySignalListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[ErrorResponse | InventorySignalListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    variant_id: list[int] | Unset = UNSET,
    stock_risk: GetAllInventorySignalsStockRisk | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> Response[ErrorResponse | InventorySignalListResponse]:
    """List inventory replenishment signals

     Returns a list of inventory replenishment signals, one per variant. Signals are account-wide, summed
      across all locations.

      Only variants with demand in the last 30 days have a row, so a variant_id filter can return fewer
    rows
      than ids requested. A missing row means no recent demand, not a missing variant - use /inventory
    for a
      full listing.

    Args:
        variant_id (list[int] | Unset):
        stock_risk (GetAllInventorySignalsStockRisk | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | InventorySignalListResponse]
    """

    kwargs = _get_kwargs(
        variant_id=variant_id,
        stock_risk=stock_risk,
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
    variant_id: list[int] | Unset = UNSET,
    stock_risk: GetAllInventorySignalsStockRisk | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> ErrorResponse | InventorySignalListResponse | None:
    """List inventory replenishment signals

     Returns a list of inventory replenishment signals, one per variant. Signals are account-wide, summed
      across all locations.

      Only variants with demand in the last 30 days have a row, so a variant_id filter can return fewer
    rows
      than ids requested. A missing row means no recent demand, not a missing variant - use /inventory
    for a
      full listing.

    Args:
        variant_id (list[int] | Unset):
        stock_risk (GetAllInventorySignalsStockRisk | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | InventorySignalListResponse
    """

    return sync_detailed(
        client=client,
        variant_id=variant_id,
        stock_risk=stock_risk,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    variant_id: list[int] | Unset = UNSET,
    stock_risk: GetAllInventorySignalsStockRisk | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> Response[ErrorResponse | InventorySignalListResponse]:
    """List inventory replenishment signals

     Returns a list of inventory replenishment signals, one per variant. Signals are account-wide, summed
      across all locations.

      Only variants with demand in the last 30 days have a row, so a variant_id filter can return fewer
    rows
      than ids requested. A missing row means no recent demand, not a missing variant - use /inventory
    for a
      full listing.

    Args:
        variant_id (list[int] | Unset):
        stock_risk (GetAllInventorySignalsStockRisk | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | InventorySignalListResponse]
    """

    kwargs = _get_kwargs(
        variant_id=variant_id,
        stock_risk=stock_risk,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    variant_id: list[int] | Unset = UNSET,
    stock_risk: GetAllInventorySignalsStockRisk | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> ErrorResponse | InventorySignalListResponse | None:
    """List inventory replenishment signals

     Returns a list of inventory replenishment signals, one per variant. Signals are account-wide, summed
      across all locations.

      Only variants with demand in the last 30 days have a row, so a variant_id filter can return fewer
    rows
      than ids requested. A missing row means no recent demand, not a missing variant - use /inventory
    for a
      full listing.

    Args:
        variant_id (list[int] | Unset):
        stock_risk (GetAllInventorySignalsStockRisk | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | InventorySignalListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            variant_id=variant_id,
            stock_risk=stock_risk,
            limit=limit,
            page=page,
        )
    ).parsed
