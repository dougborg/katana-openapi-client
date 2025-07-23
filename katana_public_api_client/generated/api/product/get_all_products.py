import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_products_extend_item import GetAllProductsExtendItem
from ...models.get_all_products_response_401 import GetAllProductsResponse401
from ...models.get_all_products_response_429 import GetAllProductsResponse429
from ...models.get_all_products_response_500 import GetAllProductsResponse500
from ...models.product_list_response import ProductListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    uom: Unset | str = UNSET,
    is_sellable: Unset | bool = UNSET,
    is_producible: Unset | bool = UNSET,
    is_purchasable: Unset | bool = UNSET,
    is_auto_assembly: Unset | bool = UNSET,
    default_supplier_id: Unset | int = UNSET,
    batch_tracked: Unset | bool = UNSET,
    serial_tracked: Unset | bool = UNSET,
    operations_in_sequence: Unset | bool = UNSET,
    purchase_uom: Unset | str = UNSET,
    purchase_uom_conversion_rate: Unset | float = UNSET,
    extend: Unset | list[GetAllProductsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
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

    params["name"] = name

    params["uom"] = uom

    params["is_sellable"] = is_sellable

    params["is_producible"] = is_producible

    params["is_purchasable"] = is_purchasable

    params["is_auto_assembly"] = is_auto_assembly

    params["default_supplier_id"] = default_supplier_id

    params["batch_tracked"] = batch_tracked

    params["serial_tracked"] = serial_tracked

    params["operations_in_sequence"] = operations_in_sequence

    params["purchase_uom"] = purchase_uom

    params["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params["include_deleted"] = include_deleted

    params["include_archived"] = include_archived

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
        "url": "/products",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
    | None
):
    if response.status_code == 200:
        response_200 = ProductListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllProductsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllProductsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllProductsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
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
    name: Unset | str = UNSET,
    uom: Unset | str = UNSET,
    is_sellable: Unset | bool = UNSET,
    is_producible: Unset | bool = UNSET,
    is_purchasable: Unset | bool = UNSET,
    is_auto_assembly: Unset | bool = UNSET,
    default_supplier_id: Unset | int = UNSET,
    batch_tracked: Unset | bool = UNSET,
    serial_tracked: Unset | bool = UNSET,
    operations_in_sequence: Unset | bool = UNSET,
    purchase_uom: Unset | str = UNSET,
    purchase_uom_conversion_rate: Unset | float = UNSET,
    extend: Unset | list[GetAllProductsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
]:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        uom (Union[Unset, str]):
        is_sellable (Union[Unset, bool]):
        is_producible (Union[Unset, bool]):
        is_purchasable (Union[Unset, bool]):
        is_auto_assembly (Union[Unset, bool]):
        default_supplier_id (Union[Unset, int]):
        batch_tracked (Union[Unset, bool]):
        serial_tracked (Union[Unset, bool]):
        operations_in_sequence (Union[Unset, bool]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        extend (Union[Unset, list[GetAllProductsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        include_archived (Union[Unset, bool]):
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
        Response[Union[GetAllProductsResponse401, GetAllProductsResponse429, GetAllProductsResponse500, ProductListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        is_producible=is_producible,
        is_purchasable=is_purchasable,
        is_auto_assembly=is_auto_assembly,
        default_supplier_id=default_supplier_id,
        batch_tracked=batch_tracked,
        serial_tracked=serial_tracked,
        operations_in_sequence=operations_in_sequence,
        purchase_uom=purchase_uom,
        purchase_uom_conversion_rate=purchase_uom_conversion_rate,
        extend=extend,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: Unset | str = UNSET,
    uom: Unset | str = UNSET,
    is_sellable: Unset | bool = UNSET,
    is_producible: Unset | bool = UNSET,
    is_purchasable: Unset | bool = UNSET,
    is_auto_assembly: Unset | bool = UNSET,
    default_supplier_id: Unset | int = UNSET,
    batch_tracked: Unset | bool = UNSET,
    serial_tracked: Unset | bool = UNSET,
    operations_in_sequence: Unset | bool = UNSET,
    purchase_uom: Unset | str = UNSET,
    purchase_uom_conversion_rate: Unset | float = UNSET,
    extend: Unset | list[GetAllProductsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
    | None
):
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        uom (Union[Unset, str]):
        is_sellable (Union[Unset, bool]):
        is_producible (Union[Unset, bool]):
        is_purchasable (Union[Unset, bool]):
        is_auto_assembly (Union[Unset, bool]):
        default_supplier_id (Union[Unset, int]):
        batch_tracked (Union[Unset, bool]):
        serial_tracked (Union[Unset, bool]):
        operations_in_sequence (Union[Unset, bool]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        extend (Union[Unset, list[GetAllProductsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        include_archived (Union[Unset, bool]):
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
        Union[GetAllProductsResponse401, GetAllProductsResponse429, GetAllProductsResponse500, ProductListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        is_producible=is_producible,
        is_purchasable=is_purchasable,
        is_auto_assembly=is_auto_assembly,
        default_supplier_id=default_supplier_id,
        batch_tracked=batch_tracked,
        serial_tracked=serial_tracked,
        operations_in_sequence=operations_in_sequence,
        purchase_uom=purchase_uom,
        purchase_uom_conversion_rate=purchase_uom_conversion_rate,
        extend=extend,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: Unset | str = UNSET,
    uom: Unset | str = UNSET,
    is_sellable: Unset | bool = UNSET,
    is_producible: Unset | bool = UNSET,
    is_purchasable: Unset | bool = UNSET,
    is_auto_assembly: Unset | bool = UNSET,
    default_supplier_id: Unset | int = UNSET,
    batch_tracked: Unset | bool = UNSET,
    serial_tracked: Unset | bool = UNSET,
    operations_in_sequence: Unset | bool = UNSET,
    purchase_uom: Unset | str = UNSET,
    purchase_uom_conversion_rate: Unset | float = UNSET,
    extend: Unset | list[GetAllProductsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
]:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        uom (Union[Unset, str]):
        is_sellable (Union[Unset, bool]):
        is_producible (Union[Unset, bool]):
        is_purchasable (Union[Unset, bool]):
        is_auto_assembly (Union[Unset, bool]):
        default_supplier_id (Union[Unset, int]):
        batch_tracked (Union[Unset, bool]):
        serial_tracked (Union[Unset, bool]):
        operations_in_sequence (Union[Unset, bool]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        extend (Union[Unset, list[GetAllProductsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        include_archived (Union[Unset, bool]):
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
        Response[Union[GetAllProductsResponse401, GetAllProductsResponse429, GetAllProductsResponse500, ProductListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        is_producible=is_producible,
        is_purchasable=is_purchasable,
        is_auto_assembly=is_auto_assembly,
        default_supplier_id=default_supplier_id,
        batch_tracked=batch_tracked,
        serial_tracked=serial_tracked,
        operations_in_sequence=operations_in_sequence,
        purchase_uom=purchase_uom,
        purchase_uom_conversion_rate=purchase_uom_conversion_rate,
        extend=extend,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: Unset | str = UNSET,
    uom: Unset | str = UNSET,
    is_sellable: Unset | bool = UNSET,
    is_producible: Unset | bool = UNSET,
    is_purchasable: Unset | bool = UNSET,
    is_auto_assembly: Unset | bool = UNSET,
    default_supplier_id: Unset | int = UNSET,
    batch_tracked: Unset | bool = UNSET,
    serial_tracked: Unset | bool = UNSET,
    operations_in_sequence: Unset | bool = UNSET,
    purchase_uom: Unset | str = UNSET,
    purchase_uom_conversion_rate: Unset | float = UNSET,
    extend: Unset | list[GetAllProductsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllProductsResponse401
    | GetAllProductsResponse429
    | GetAllProductsResponse500
    | ProductListResponse
    | None
):
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        uom (Union[Unset, str]):
        is_sellable (Union[Unset, bool]):
        is_producible (Union[Unset, bool]):
        is_purchasable (Union[Unset, bool]):
        is_auto_assembly (Union[Unset, bool]):
        default_supplier_id (Union[Unset, int]):
        batch_tracked (Union[Unset, bool]):
        serial_tracked (Union[Unset, bool]):
        operations_in_sequence (Union[Unset, bool]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        extend (Union[Unset, list[GetAllProductsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        include_archived (Union[Unset, bool]):
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
        Union[GetAllProductsResponse401, GetAllProductsResponse429, GetAllProductsResponse500, ProductListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            name=name,
            uom=uom,
            is_sellable=is_sellable,
            is_producible=is_producible,
            is_purchasable=is_purchasable,
            is_auto_assembly=is_auto_assembly,
            default_supplier_id=default_supplier_id,
            batch_tracked=batch_tracked,
            serial_tracked=serial_tracked,
            operations_in_sequence=operations_in_sequence,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            extend=extend,
            include_deleted=include_deleted,
            include_archived=include_archived,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
