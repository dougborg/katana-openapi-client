import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_variants_extend_item import GetAllVariantsExtendItem
from ...models.variant_list_response import VariantListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    material_id: int | Unset = UNSET,
    sku: list[str] | Unset = UNSET,
    sales_price: float | Unset = UNSET,
    purchase_price: float | Unset = UNSET,
    internal_barcode: str | Unset = UNSET,
    registered_barcode: str | Unset = UNSET,
    supplier_item_codes: list[str] | Unset = UNSET,
    extend: list[GetAllVariantsExtendItem] | Unset = UNSET,
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

    params["product_id"] = product_id

    params["material_id"] = material_id

    json_sku: list[str] | Unset = UNSET
    if not isinstance(sku, Unset):
        json_sku = sku

    params["sku"] = json_sku

    params["sales_price"] = sales_price

    params["purchase_price"] = purchase_price

    params["internal_barcode"] = internal_barcode

    params["registered_barcode"] = registered_barcode

    json_supplier_item_codes: list[str] | Unset = UNSET
    if not isinstance(supplier_item_codes, Unset):
        json_supplier_item_codes = supplier_item_codes

    params["supplier_item_codes"] = json_supplier_item_codes

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
        "url": "/variants",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | VariantListResponse | None:
    if response.status_code == 200:
        response_200 = VariantListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | VariantListResponse]:
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
    product_id: int | Unset = UNSET,
    material_id: int | Unset = UNSET,
    sku: list[str] | Unset = UNSET,
    sales_price: float | Unset = UNSET,
    purchase_price: float | Unset = UNSET,
    internal_barcode: str | Unset = UNSET,
    registered_barcode: str | Unset = UNSET,
    supplier_item_codes: list[str] | Unset = UNSET,
    extend: list[GetAllVariantsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | VariantListResponse]:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (list[int] | Unset):
        product_id (int | Unset):
        material_id (int | Unset):
        sku (list[str] | Unset):
        sales_price (float | Unset):
        purchase_price (float | Unset):
        internal_barcode (str | Unset):
        registered_barcode (str | Unset):
        supplier_item_codes (list[str] | Unset):
        extend (list[GetAllVariantsExtendItem] | Unset):
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
        Response[ErrorResponse | VariantListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        product_id=product_id,
        material_id=material_id,
        sku=sku,
        sales_price=sales_price,
        purchase_price=purchase_price,
        internal_barcode=internal_barcode,
        registered_barcode=registered_barcode,
        supplier_item_codes=supplier_item_codes,
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
    product_id: int | Unset = UNSET,
    material_id: int | Unset = UNSET,
    sku: list[str] | Unset = UNSET,
    sales_price: float | Unset = UNSET,
    purchase_price: float | Unset = UNSET,
    internal_barcode: str | Unset = UNSET,
    registered_barcode: str | Unset = UNSET,
    supplier_item_codes: list[str] | Unset = UNSET,
    extend: list[GetAllVariantsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | VariantListResponse | None:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (list[int] | Unset):
        product_id (int | Unset):
        material_id (int | Unset):
        sku (list[str] | Unset):
        sales_price (float | Unset):
        purchase_price (float | Unset):
        internal_barcode (str | Unset):
        registered_barcode (str | Unset):
        supplier_item_codes (list[str] | Unset):
        extend (list[GetAllVariantsExtendItem] | Unset):
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
        ErrorResponse | VariantListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        product_id=product_id,
        material_id=material_id,
        sku=sku,
        sales_price=sales_price,
        purchase_price=purchase_price,
        internal_barcode=internal_barcode,
        registered_barcode=registered_barcode,
        supplier_item_codes=supplier_item_codes,
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
    product_id: int | Unset = UNSET,
    material_id: int | Unset = UNSET,
    sku: list[str] | Unset = UNSET,
    sales_price: float | Unset = UNSET,
    purchase_price: float | Unset = UNSET,
    internal_barcode: str | Unset = UNSET,
    registered_barcode: str | Unset = UNSET,
    supplier_item_codes: list[str] | Unset = UNSET,
    extend: list[GetAllVariantsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | VariantListResponse]:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (list[int] | Unset):
        product_id (int | Unset):
        material_id (int | Unset):
        sku (list[str] | Unset):
        sales_price (float | Unset):
        purchase_price (float | Unset):
        internal_barcode (str | Unset):
        registered_barcode (str | Unset):
        supplier_item_codes (list[str] | Unset):
        extend (list[GetAllVariantsExtendItem] | Unset):
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
        Response[ErrorResponse | VariantListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        product_id=product_id,
        material_id=material_id,
        sku=sku,
        sales_price=sales_price,
        purchase_price=purchase_price,
        internal_barcode=internal_barcode,
        registered_barcode=registered_barcode,
        supplier_item_codes=supplier_item_codes,
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
    product_id: int | Unset = UNSET,
    material_id: int | Unset = UNSET,
    sku: list[str] | Unset = UNSET,
    sales_price: float | Unset = UNSET,
    purchase_price: float | Unset = UNSET,
    internal_barcode: str | Unset = UNSET,
    registered_barcode: str | Unset = UNSET,
    supplier_item_codes: list[str] | Unset = UNSET,
    extend: list[GetAllVariantsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | VariantListResponse | None:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (list[int] | Unset):
        product_id (int | Unset):
        material_id (int | Unset):
        sku (list[str] | Unset):
        sales_price (float | Unset):
        purchase_price (float | Unset):
        internal_barcode (str | Unset):
        registered_barcode (str | Unset):
        supplier_item_codes (list[str] | Unset):
        extend (list[GetAllVariantsExtendItem] | Unset):
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
        ErrorResponse | VariantListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            product_id=product_id,
            material_id=material_id,
            sku=sku,
            sales_price=sales_price,
            purchase_price=purchase_price,
            internal_barcode=internal_barcode,
            registered_barcode=registered_barcode,
            supplier_item_codes=supplier_item_codes,
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
