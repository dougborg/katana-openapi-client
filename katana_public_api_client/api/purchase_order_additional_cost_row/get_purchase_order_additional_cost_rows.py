import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_purchase_order_additional_cost_rows_distribution_method import (
    GetPurchaseOrderAdditionalCostRowsDistributionMethod,
)
from ...models.purchase_order_additional_cost_row_list_response import (
    PurchaseOrderAdditionalCostRowListResponse,
)


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    group_id: float | Unset = UNSET,
    additional_cost_id: float | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    currency: str | Unset = UNSET,
    distribution_method: GetPurchaseOrderAdditionalCostRowsDistributionMethod
    | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["group_id"] = group_id

    params["additional_cost_id"] = additional_cost_id

    params["tax_rate_id"] = tax_rate_id

    params["currency"] = currency

    json_distribution_method: str | Unset = UNSET
    if not isinstance(distribution_method, Unset):
        json_distribution_method = distribution_method.value

    params["distribution_method"] = json_distribution_method

    params["include_deleted"] = include_deleted

    params["limit"] = limit

    params["page"] = page

    json_created_at_min: str | Unset = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: str | Unset = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: str | Unset = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: str | Unset = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/po_additional_cost_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PurchaseOrderAdditionalCostRowListResponse | None:
    if response.status_code == 200:
        response_200 = PurchaseOrderAdditionalCostRowListResponse.from_dict(
            response.json()
        )

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
) -> Response[ErrorResponse | PurchaseOrderAdditionalCostRowListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: list[int] | Unset = UNSET,
    group_id: float | Unset = UNSET,
    additional_cost_id: float | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    currency: str | Unset = UNSET,
    distribution_method: GetPurchaseOrderAdditionalCostRowsDistributionMethod
    | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | PurchaseOrderAdditionalCostRowListResponse]:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (list[int] | Unset):
        group_id (float | Unset):
        additional_cost_id (float | Unset):
        tax_rate_id (float | Unset):
        currency (str | Unset):
        distribution_method (GetPurchaseOrderAdditionalCostRowsDistributionMethod | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | PurchaseOrderAdditionalCostRowListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        group_id=group_id,
        additional_cost_id=additional_cost_id,
        tax_rate_id=tax_rate_id,
        currency=currency,
        distribution_method=distribution_method,
        include_deleted=include_deleted,
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
    ids: list[int] | Unset = UNSET,
    group_id: float | Unset = UNSET,
    additional_cost_id: float | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    currency: str | Unset = UNSET,
    distribution_method: GetPurchaseOrderAdditionalCostRowsDistributionMethod
    | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | PurchaseOrderAdditionalCostRowListResponse | None:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (list[int] | Unset):
        group_id (float | Unset):
        additional_cost_id (float | Unset):
        tax_rate_id (float | Unset):
        currency (str | Unset):
        distribution_method (GetPurchaseOrderAdditionalCostRowsDistributionMethod | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | PurchaseOrderAdditionalCostRowListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        group_id=group_id,
        additional_cost_id=additional_cost_id,
        tax_rate_id=tax_rate_id,
        currency=currency,
        distribution_method=distribution_method,
        include_deleted=include_deleted,
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
    ids: list[int] | Unset = UNSET,
    group_id: float | Unset = UNSET,
    additional_cost_id: float | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    currency: str | Unset = UNSET,
    distribution_method: GetPurchaseOrderAdditionalCostRowsDistributionMethod
    | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | PurchaseOrderAdditionalCostRowListResponse]:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (list[int] | Unset):
        group_id (float | Unset):
        additional_cost_id (float | Unset):
        tax_rate_id (float | Unset):
        currency (str | Unset):
        distribution_method (GetPurchaseOrderAdditionalCostRowsDistributionMethod | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | PurchaseOrderAdditionalCostRowListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        group_id=group_id,
        additional_cost_id=additional_cost_id,
        tax_rate_id=tax_rate_id,
        currency=currency,
        distribution_method=distribution_method,
        include_deleted=include_deleted,
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
    ids: list[int] | Unset = UNSET,
    group_id: float | Unset = UNSET,
    additional_cost_id: float | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    currency: str | Unset = UNSET,
    distribution_method: GetPurchaseOrderAdditionalCostRowsDistributionMethod
    | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | PurchaseOrderAdditionalCostRowListResponse | None:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (list[int] | Unset):
        group_id (float | Unset):
        additional_cost_id (float | Unset):
        tax_rate_id (float | Unset):
        currency (str | Unset):
        distribution_method (GetPurchaseOrderAdditionalCostRowsDistributionMethod | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | PurchaseOrderAdditionalCostRowListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            group_id=group_id,
            additional_cost_id=additional_cost_id,
            tax_rate_id=tax_rate_id,
            currency=currency,
            distribution_method=distribution_method,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
