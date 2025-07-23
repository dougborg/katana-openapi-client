from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_outsourced_purchase_order_recipe_rows_response_401 import (
    GetOutsourcedPurchaseOrderRecipeRowsResponse401,
)
from ...models.get_outsourced_purchase_order_recipe_rows_response_429 import (
    GetOutsourcedPurchaseOrderRecipeRowsResponse429,
)
from ...models.get_outsourced_purchase_order_recipe_rows_response_500 import (
    GetOutsourcedPurchaseOrderRecipeRowsResponse500,
)
from ...models.outsourced_purchase_order_recipe_row_list_response import (
    OutsourcedPurchaseOrderRecipeRowListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    outsourced_purchase_order_id: Unset | int = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["outsourced_purchase_order_id"] = outsourced_purchase_order_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/outsourced_purchase_order_recipe_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = OutsourcedPurchaseOrderRecipeRowListResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = GetOutsourcedPurchaseOrderRecipeRowsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetOutsourcedPurchaseOrderRecipeRowsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetOutsourcedPurchaseOrderRecipeRowsResponse500.from_dict(
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
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    outsourced_purchase_order_id: Unset | int = UNSET,
) -> Response[
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
]:
    """List all outsourced purchase order recipe rows

     Retrieves a list of outsourced purchase order recipe rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        outsourced_purchase_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetOutsourcedPurchaseOrderRecipeRowsResponse401, GetOutsourcedPurchaseOrderRecipeRowsResponse429, GetOutsourcedPurchaseOrderRecipeRowsResponse500, OutsourcedPurchaseOrderRecipeRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        outsourced_purchase_order_id=outsourced_purchase_order_id,
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
    ids: Unset | list[int] = UNSET,
    outsourced_purchase_order_id: Unset | int = UNSET,
) -> (
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
    | None
):
    """List all outsourced purchase order recipe rows

     Retrieves a list of outsourced purchase order recipe rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        outsourced_purchase_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetOutsourcedPurchaseOrderRecipeRowsResponse401, GetOutsourcedPurchaseOrderRecipeRowsResponse429, GetOutsourcedPurchaseOrderRecipeRowsResponse500, OutsourcedPurchaseOrderRecipeRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        outsourced_purchase_order_id=outsourced_purchase_order_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    outsourced_purchase_order_id: Unset | int = UNSET,
) -> Response[
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
]:
    """List all outsourced purchase order recipe rows

     Retrieves a list of outsourced purchase order recipe rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        outsourced_purchase_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetOutsourcedPurchaseOrderRecipeRowsResponse401, GetOutsourcedPurchaseOrderRecipeRowsResponse429, GetOutsourcedPurchaseOrderRecipeRowsResponse500, OutsourcedPurchaseOrderRecipeRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        outsourced_purchase_order_id=outsourced_purchase_order_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    outsourced_purchase_order_id: Unset | int = UNSET,
) -> (
    GetOutsourcedPurchaseOrderRecipeRowsResponse401
    | GetOutsourcedPurchaseOrderRecipeRowsResponse429
    | GetOutsourcedPurchaseOrderRecipeRowsResponse500
    | OutsourcedPurchaseOrderRecipeRowListResponse
    | None
):
    """List all outsourced purchase order recipe rows

     Retrieves a list of outsourced purchase order recipe rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        outsourced_purchase_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetOutsourcedPurchaseOrderRecipeRowsResponse401, GetOutsourcedPurchaseOrderRecipeRowsResponse429, GetOutsourcedPurchaseOrderRecipeRowsResponse500, OutsourcedPurchaseOrderRecipeRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            outsourced_purchase_order_id=outsourced_purchase_order_id,
        )
    ).parsed
