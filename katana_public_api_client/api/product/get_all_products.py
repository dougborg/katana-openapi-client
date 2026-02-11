import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_products_extend_item import GetAllProductsExtendItem
from ...models.product_list_response import ProductListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    is_producible: bool | Unset = UNSET,
    is_purchasable: bool | Unset = UNSET,
    is_auto_assembly: bool | Unset = UNSET,
    default_supplier_id: int | Unset = UNSET,
    batch_tracked: bool | Unset = UNSET,
    serial_tracked: bool | Unset = UNSET,
    operations_in_sequence: bool | Unset = UNSET,
    purchase_uom: str | Unset = UNSET,
    purchase_uom_conversion_rate: float | Unset = UNSET,
    extend: list[GetAllProductsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
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

    json_extend: list[str] | Unset = UNSET
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
        "url": "/products",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ProductListResponse | None:
    if response.status_code == 200:
        response_200 = ProductListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | ProductListResponse]:
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
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    is_producible: bool | Unset = UNSET,
    is_purchasable: bool | Unset = UNSET,
    is_auto_assembly: bool | Unset = UNSET,
    default_supplier_id: int | Unset = UNSET,
    batch_tracked: bool | Unset = UNSET,
    serial_tracked: bool | Unset = UNSET,
    operations_in_sequence: bool | Unset = UNSET,
    purchase_uom: str | Unset = UNSET,
    purchase_uom_conversion_rate: float | Unset = UNSET,
    extend: list[GetAllProductsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ProductListResponse]:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        is_producible (bool | Unset):
        is_purchasable (bool | Unset):
        is_auto_assembly (bool | Unset):
        default_supplier_id (int | Unset):
        batch_tracked (bool | Unset):
        serial_tracked (bool | Unset):
        operations_in_sequence (bool | Unset):
        purchase_uom (str | Unset):
        purchase_uom_conversion_rate (float | Unset):
        extend (list[GetAllProductsExtendItem] | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        Response[ErrorResponse | ProductListResponse]
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    is_producible: bool | Unset = UNSET,
    is_purchasable: bool | Unset = UNSET,
    is_auto_assembly: bool | Unset = UNSET,
    default_supplier_id: int | Unset = UNSET,
    batch_tracked: bool | Unset = UNSET,
    serial_tracked: bool | Unset = UNSET,
    operations_in_sequence: bool | Unset = UNSET,
    purchase_uom: str | Unset = UNSET,
    purchase_uom_conversion_rate: float | Unset = UNSET,
    extend: list[GetAllProductsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ProductListResponse | None:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        is_producible (bool | Unset):
        is_purchasable (bool | Unset):
        is_auto_assembly (bool | Unset):
        default_supplier_id (int | Unset):
        batch_tracked (bool | Unset):
        serial_tracked (bool | Unset):
        operations_in_sequence (bool | Unset):
        purchase_uom (str | Unset):
        purchase_uom_conversion_rate (float | Unset):
        extend (list[GetAllProductsExtendItem] | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        ErrorResponse | ProductListResponse
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    is_producible: bool | Unset = UNSET,
    is_purchasable: bool | Unset = UNSET,
    is_auto_assembly: bool | Unset = UNSET,
    default_supplier_id: int | Unset = UNSET,
    batch_tracked: bool | Unset = UNSET,
    serial_tracked: bool | Unset = UNSET,
    operations_in_sequence: bool | Unset = UNSET,
    purchase_uom: str | Unset = UNSET,
    purchase_uom_conversion_rate: float | Unset = UNSET,
    extend: list[GetAllProductsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ProductListResponse]:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        is_producible (bool | Unset):
        is_purchasable (bool | Unset):
        is_auto_assembly (bool | Unset):
        default_supplier_id (int | Unset):
        batch_tracked (bool | Unset):
        serial_tracked (bool | Unset):
        operations_in_sequence (bool | Unset):
        purchase_uom (str | Unset):
        purchase_uom_conversion_rate (float | Unset):
        extend (list[GetAllProductsExtendItem] | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        Response[ErrorResponse | ProductListResponse]
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    is_producible: bool | Unset = UNSET,
    is_purchasable: bool | Unset = UNSET,
    is_auto_assembly: bool | Unset = UNSET,
    default_supplier_id: int | Unset = UNSET,
    batch_tracked: bool | Unset = UNSET,
    serial_tracked: bool | Unset = UNSET,
    operations_in_sequence: bool | Unset = UNSET,
    purchase_uom: str | Unset = UNSET,
    purchase_uom_conversion_rate: float | Unset = UNSET,
    extend: list[GetAllProductsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ProductListResponse | None:
    """List all products

     Returns a list of products you've previously created. The products are returned in sorted order,
        with the most recent products appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        is_producible (bool | Unset):
        is_purchasable (bool | Unset):
        is_auto_assembly (bool | Unset):
        default_supplier_id (int | Unset):
        batch_tracked (bool | Unset):
        serial_tracked (bool | Unset):
        operations_in_sequence (bool | Unset):
        purchase_uom (str | Unset):
        purchase_uom_conversion_rate (float | Unset):
        extend (list[GetAllProductsExtendItem] | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        ErrorResponse | ProductListResponse
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
