import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_variants_extend_item import GetAllVariantsExtendItem
from ...models.get_all_variants_response_401 import GetAllVariantsResponse401
from ...models.get_all_variants_response_429 import GetAllVariantsResponse429
from ...models.get_all_variants_response_500 import GetAllVariantsResponse500
from ...models.variant_list_response import VariantListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    product_id: Unset | int = UNSET,
    material_id: Unset | int = UNSET,
    sku: Unset | str = UNSET,
    sales_price: Unset | float = UNSET,
    purchase_price: Unset | float = UNSET,
    internal_barcode: Unset | str = UNSET,
    registered_barcode: Unset | str = UNSET,
    supplier_item_codes: Unset | list[str] = UNSET,
    extend: Unset | list[GetAllVariantsExtendItem] = UNSET,
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

    params["product_id"] = product_id

    params["material_id"] = material_id

    params["sku"] = sku

    params["sales_price"] = sales_price

    params["purchase_price"] = purchase_price

    params["internal_barcode"] = internal_barcode

    params["registered_barcode"] = registered_barcode

    json_supplier_item_codes: Unset | list[str] = UNSET
    if not isinstance(supplier_item_codes, Unset):
        json_supplier_item_codes = supplier_item_codes

    params["supplier_item_codes"] = json_supplier_item_codes

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
        "url": "/variants",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
    | None
):
    if response.status_code == 200:
        response_200 = VariantListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllVariantsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllVariantsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllVariantsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
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
    product_id: Unset | int = UNSET,
    material_id: Unset | int = UNSET,
    sku: Unset | str = UNSET,
    sales_price: Unset | float = UNSET,
    purchase_price: Unset | float = UNSET,
    internal_barcode: Unset | str = UNSET,
    registered_barcode: Unset | str = UNSET,
    supplier_item_codes: Unset | list[str] = UNSET,
    extend: Unset | list[GetAllVariantsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
]:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        product_id (Union[Unset, int]):
        material_id (Union[Unset, int]):
        sku (Union[Unset, str]):
        sales_price (Union[Unset, float]):
        purchase_price (Union[Unset, float]):
        internal_barcode (Union[Unset, str]):
        registered_barcode (Union[Unset, str]):
        supplier_item_codes (Union[Unset, list[str]]):
        extend (Union[Unset, list[GetAllVariantsExtendItem]]):
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
        Response[Union[GetAllVariantsResponse401, GetAllVariantsResponse429, GetAllVariantsResponse500, VariantListResponse]]
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
    ids: Unset | list[int] = UNSET,
    product_id: Unset | int = UNSET,
    material_id: Unset | int = UNSET,
    sku: Unset | str = UNSET,
    sales_price: Unset | float = UNSET,
    purchase_price: Unset | float = UNSET,
    internal_barcode: Unset | str = UNSET,
    registered_barcode: Unset | str = UNSET,
    supplier_item_codes: Unset | list[str] = UNSET,
    extend: Unset | list[GetAllVariantsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
    | None
):
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        product_id (Union[Unset, int]):
        material_id (Union[Unset, int]):
        sku (Union[Unset, str]):
        sales_price (Union[Unset, float]):
        purchase_price (Union[Unset, float]):
        internal_barcode (Union[Unset, str]):
        registered_barcode (Union[Unset, str]):
        supplier_item_codes (Union[Unset, list[str]]):
        extend (Union[Unset, list[GetAllVariantsExtendItem]]):
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
        Union[GetAllVariantsResponse401, GetAllVariantsResponse429, GetAllVariantsResponse500, VariantListResponse]
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
    ids: Unset | list[int] = UNSET,
    product_id: Unset | int = UNSET,
    material_id: Unset | int = UNSET,
    sku: Unset | str = UNSET,
    sales_price: Unset | float = UNSET,
    purchase_price: Unset | float = UNSET,
    internal_barcode: Unset | str = UNSET,
    registered_barcode: Unset | str = UNSET,
    supplier_item_codes: Unset | list[str] = UNSET,
    extend: Unset | list[GetAllVariantsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
]:
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        product_id (Union[Unset, int]):
        material_id (Union[Unset, int]):
        sku (Union[Unset, str]):
        sales_price (Union[Unset, float]):
        purchase_price (Union[Unset, float]):
        internal_barcode (Union[Unset, str]):
        registered_barcode (Union[Unset, str]):
        supplier_item_codes (Union[Unset, list[str]]):
        extend (Union[Unset, list[GetAllVariantsExtendItem]]):
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
        Response[Union[GetAllVariantsResponse401, GetAllVariantsResponse429, GetAllVariantsResponse500, VariantListResponse]]
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
    ids: Unset | list[int] = UNSET,
    product_id: Unset | int = UNSET,
    material_id: Unset | int = UNSET,
    sku: Unset | str = UNSET,
    sales_price: Unset | float = UNSET,
    purchase_price: Unset | float = UNSET,
    internal_barcode: Unset | str = UNSET,
    registered_barcode: Unset | str = UNSET,
    supplier_item_codes: Unset | list[str] = UNSET,
    extend: Unset | list[GetAllVariantsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    include_archived: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllVariantsResponse401
    | GetAllVariantsResponse429
    | GetAllVariantsResponse500
    | VariantListResponse
    | None
):
    """List all variants

     Returns a list of variants you've previously created. The variants are returned in sorted order,
        with the most recent variants appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        product_id (Union[Unset, int]):
        material_id (Union[Unset, int]):
        sku (Union[Unset, str]):
        sales_price (Union[Unset, float]):
        purchase_price (Union[Unset, float]):
        internal_barcode (Union[Unset, str]):
        registered_barcode (Union[Unset, str]):
        supplier_item_codes (Union[Unset, list[str]]):
        extend (Union[Unset, list[GetAllVariantsExtendItem]]):
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
        Union[GetAllVariantsResponse401, GetAllVariantsResponse429, GetAllVariantsResponse500, VariantListResponse]
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
