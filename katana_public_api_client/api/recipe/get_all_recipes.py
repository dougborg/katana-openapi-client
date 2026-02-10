import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.recipe_list_response import RecipeListResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    ingredient_variant_id: int | Unset = UNSET,
    product_variant_ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    recipe_row_id: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

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

    params["ingredient_variant_id"] = ingredient_variant_id

    json_product_variant_ids: list[int] | Unset = UNSET
    if not isinstance(product_variant_ids, Unset):
        json_product_variant_ids = product_variant_ids

    params["product_variant_ids"] = json_product_variant_ids

    params["product_id"] = product_id

    params["recipe_row_id"] = recipe_row_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/recipes",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | RecipeListResponse | None:
    if response.status_code == 200:
        response_200 = RecipeListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | RecipeListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    ingredient_variant_id: int | Unset = UNSET,
    product_variant_ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    recipe_row_id: int | Unset = UNSET,
) -> Response[ErrorResponse | RecipeListResponse]:
    """Get all recipes

     Returns a list of all recipe rows. The recipes endpoint is deprecated in favor of BOM rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        ingredient_variant_id (int | Unset):
        product_variant_ids (list[int] | Unset):
        product_id (int | Unset):
        recipe_row_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | RecipeListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ingredient_variant_id=ingredient_variant_id,
        product_variant_ids=product_variant_ids,
        product_id=product_id,
        recipe_row_id=recipe_row_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    ingredient_variant_id: int | Unset = UNSET,
    product_variant_ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    recipe_row_id: int | Unset = UNSET,
) -> ErrorResponse | RecipeListResponse | None:
    """Get all recipes

     Returns a list of all recipe rows. The recipes endpoint is deprecated in favor of BOM rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        ingredient_variant_id (int | Unset):
        product_variant_ids (list[int] | Unset):
        product_id (int | Unset):
        recipe_row_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | RecipeListResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ingredient_variant_id=ingredient_variant_id,
        product_variant_ids=product_variant_ids,
        product_id=product_id,
        recipe_row_id=recipe_row_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    ingredient_variant_id: int | Unset = UNSET,
    product_variant_ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    recipe_row_id: int | Unset = UNSET,
) -> Response[ErrorResponse | RecipeListResponse]:
    """Get all recipes

     Returns a list of all recipe rows. The recipes endpoint is deprecated in favor of BOM rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        ingredient_variant_id (int | Unset):
        product_variant_ids (list[int] | Unset):
        product_id (int | Unset):
        recipe_row_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | RecipeListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ingredient_variant_id=ingredient_variant_id,
        product_variant_ids=product_variant_ids,
        product_id=product_id,
        recipe_row_id=recipe_row_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    ingredient_variant_id: int | Unset = UNSET,
    product_variant_ids: list[int] | Unset = UNSET,
    product_id: int | Unset = UNSET,
    recipe_row_id: int | Unset = UNSET,
) -> ErrorResponse | RecipeListResponse | None:
    """Get all recipes

     Returns a list of all recipe rows. The recipes endpoint is deprecated in favor of BOM rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        ingredient_variant_id (int | Unset):
        product_variant_ids (list[int] | Unset):
        product_id (int | Unset):
        recipe_row_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | RecipeListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            ingredient_variant_id=ingredient_variant_id,
            product_variant_ids=product_variant_ids,
            product_id=product_id,
            recipe_row_id=recipe_row_id,
        )
    ).parsed
