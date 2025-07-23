import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_purchase_order_additional_cost_rows_distribution_method import (
    GetPurchaseOrderAdditionalCostRowsDistributionMethod,
)
from ...models.get_purchase_order_additional_cost_rows_response_401 import (
    GetPurchaseOrderAdditionalCostRowsResponse401,
)
from ...models.get_purchase_order_additional_cost_rows_response_429 import (
    GetPurchaseOrderAdditionalCostRowsResponse429,
)
from ...models.get_purchase_order_additional_cost_rows_response_500 import (
    GetPurchaseOrderAdditionalCostRowsResponse500,
)
from ...models.purchase_order_additional_cost_row_list_response import (
    PurchaseOrderAdditionalCostRowListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    group_id: Unset | float = UNSET,
    additional_cost_id: Unset | float = UNSET,
    tax_rate_id: Unset | float = UNSET,
    currency: Unset | str = UNSET,
    distribution_method: Unset
    | GetPurchaseOrderAdditionalCostRowsDistributionMethod = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["group_id"] = group_id

    params["additional_cost_id"] = additional_cost_id

    params["tax_rate_id"] = tax_rate_id

    params["currency"] = currency

    json_distribution_method: Unset | str = UNSET
    if not isinstance(distribution_method, Unset):
        json_distribution_method = distribution_method.value

    params["distribution_method"] = json_distribution_method

    params["include_deleted"] = include_deleted

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
        "url": "/po_additional_cost_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderAdditionalCostRowListResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = GetPurchaseOrderAdditionalCostRowsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetPurchaseOrderAdditionalCostRowsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetPurchaseOrderAdditionalCostRowsResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
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
    ids: Unset | list[int] = UNSET,
    group_id: Unset | float = UNSET,
    additional_cost_id: Unset | float = UNSET,
    tax_rate_id: Unset | float = UNSET,
    currency: Unset | str = UNSET,
    distribution_method: Unset
    | GetPurchaseOrderAdditionalCostRowsDistributionMethod = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
]:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (Union[Unset, list[int]]):
        group_id (Union[Unset, float]):
        additional_cost_id (Union[Unset, float]):
        tax_rate_id (Union[Unset, float]):
        currency (Union[Unset, str]):
        distribution_method (Union[Unset, GetPurchaseOrderAdditionalCostRowsDistributionMethod]):
        include_deleted (Union[Unset, bool]):
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
        Response[Union[GetPurchaseOrderAdditionalCostRowsResponse401, GetPurchaseOrderAdditionalCostRowsResponse429, GetPurchaseOrderAdditionalCostRowsResponse500, PurchaseOrderAdditionalCostRowListResponse]]
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
    ids: Unset | list[int] = UNSET,
    group_id: Unset | float = UNSET,
    additional_cost_id: Unset | float = UNSET,
    tax_rate_id: Unset | float = UNSET,
    currency: Unset | str = UNSET,
    distribution_method: Unset
    | GetPurchaseOrderAdditionalCostRowsDistributionMethod = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
    | None
):
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (Union[Unset, list[int]]):
        group_id (Union[Unset, float]):
        additional_cost_id (Union[Unset, float]):
        tax_rate_id (Union[Unset, float]):
        currency (Union[Unset, str]):
        distribution_method (Union[Unset, GetPurchaseOrderAdditionalCostRowsDistributionMethod]):
        include_deleted (Union[Unset, bool]):
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
        Union[GetPurchaseOrderAdditionalCostRowsResponse401, GetPurchaseOrderAdditionalCostRowsResponse429, GetPurchaseOrderAdditionalCostRowsResponse500, PurchaseOrderAdditionalCostRowListResponse]
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
    ids: Unset | list[int] = UNSET,
    group_id: Unset | float = UNSET,
    additional_cost_id: Unset | float = UNSET,
    tax_rate_id: Unset | float = UNSET,
    currency: Unset | str = UNSET,
    distribution_method: Unset
    | GetPurchaseOrderAdditionalCostRowsDistributionMethod = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
]:
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (Union[Unset, list[int]]):
        group_id (Union[Unset, float]):
        additional_cost_id (Union[Unset, float]):
        tax_rate_id (Union[Unset, float]):
        currency (Union[Unset, str]):
        distribution_method (Union[Unset, GetPurchaseOrderAdditionalCostRowsDistributionMethod]):
        include_deleted (Union[Unset, bool]):
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
        Response[Union[GetPurchaseOrderAdditionalCostRowsResponse401, GetPurchaseOrderAdditionalCostRowsResponse429, GetPurchaseOrderAdditionalCostRowsResponse500, PurchaseOrderAdditionalCostRowListResponse]]
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
    ids: Unset | list[int] = UNSET,
    group_id: Unset | float = UNSET,
    additional_cost_id: Unset | float = UNSET,
    tax_rate_id: Unset | float = UNSET,
    currency: Unset | str = UNSET,
    distribution_method: Unset
    | GetPurchaseOrderAdditionalCostRowsDistributionMethod = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetPurchaseOrderAdditionalCostRowsResponse401
    | GetPurchaseOrderAdditionalCostRowsResponse429
    | GetPurchaseOrderAdditionalCostRowsResponse500
    | PurchaseOrderAdditionalCostRowListResponse
    | None
):
    """List all purchase order additional cost rows

     Returns a list of purchase order additional cost rows you've previously created.

    Args:
        ids (Union[Unset, list[int]]):
        group_id (Union[Unset, float]):
        additional_cost_id (Union[Unset, float]):
        tax_rate_id (Union[Unset, float]):
        currency (Union[Unset, str]):
        distribution_method (Union[Unset, GetPurchaseOrderAdditionalCostRowsDistributionMethod]):
        include_deleted (Union[Unset, bool]):
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
        Union[GetPurchaseOrderAdditionalCostRowsResponse401, GetPurchaseOrderAdditionalCostRowsResponse429, GetPurchaseOrderAdditionalCostRowsResponse500, PurchaseOrderAdditionalCostRowListResponse]
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
