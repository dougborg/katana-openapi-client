from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.bom_row_list_response import BomRowListResponse
from ...models.error_response import ErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    product_variant_id: Union[Unset, int] = UNSET,
    ingredient_variant_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["product_variant_id"] = product_variant_id

    params["ingredient_variant_id"] = ingredient_variant_id

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bom_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[BomRowListResponse, ErrorResponse]]:
    if response.status_code == 200:
        response_200 = BomRowListResponse.from_dict(response.json())

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[BomRowListResponse, ErrorResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    product_variant_id: Union[Unset, int] = UNSET,
    ingredient_variant_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Response[Union[BomRowListResponse, ErrorResponse]]:
    """List all BOM rows

     Returns a list of BOM (Bill of Materials) rows you've previously created. Product variant BOM
    consists of ingredient variants and their quantities.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        product_variant_id (Union[Unset, int]):
        ingredient_variant_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BomRowListResponse, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        product_variant_id=product_variant_id,
        ingredient_variant_id=ingredient_variant_id,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    product_variant_id: Union[Unset, int] = UNSET,
    ingredient_variant_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Optional[Union[BomRowListResponse, ErrorResponse]]:
    """List all BOM rows

     Returns a list of BOM (Bill of Materials) rows you've previously created. Product variant BOM
    consists of ingredient variants and their quantities.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        product_variant_id (Union[Unset, int]):
        ingredient_variant_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BomRowListResponse, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        product_variant_id=product_variant_id,
        ingredient_variant_id=ingredient_variant_id,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    product_variant_id: Union[Unset, int] = UNSET,
    ingredient_variant_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Response[Union[BomRowListResponse, ErrorResponse]]:
    """List all BOM rows

     Returns a list of BOM (Bill of Materials) rows you've previously created. Product variant BOM
    consists of ingredient variants and their quantities.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        product_variant_id (Union[Unset, int]):
        ingredient_variant_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BomRowListResponse, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        product_variant_id=product_variant_id,
        ingredient_variant_id=ingredient_variant_id,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    product_variant_id: Union[Unset, int] = UNSET,
    ingredient_variant_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Optional[Union[BomRowListResponse, ErrorResponse]]:
    """List all BOM rows

     Returns a list of BOM (Bill of Materials) rows you've previously created. Product variant BOM
    consists of ingredient variants and their quantities.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        product_variant_id (Union[Unset, int]):
        ingredient_variant_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BomRowListResponse, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            product_variant_id=product_variant_id,
            ingredient_variant_id=ingredient_variant_id,
            include_deleted=include_deleted,
        )
    ).parsed
