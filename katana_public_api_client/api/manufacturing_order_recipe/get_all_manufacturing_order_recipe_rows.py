import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.ingredient_availability import IngredientAvailability
from ...models.manufacturing_order_recipe_row_list_response import (
    ManufacturingOrderRecipeRowListResponse,
)


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    manufacturing_order_id: float | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
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

    params["manufacturing_order_id"] = manufacturing_order_id

    params["variant_id"] = variant_id

    json_ingredient_availability: str | Unset = UNSET
    if not isinstance(ingredient_availability, Unset):
        json_ingredient_availability = ingredient_availability.value

    params["ingredient_availability"] = json_ingredient_availability

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
        "url": "/manufacturing_order_recipe_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrderRecipeRowListResponse | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrderRecipeRowListResponse.from_dict(
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
) -> Response[ErrorResponse | ManufacturingOrderRecipeRowListResponse]:
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
    manufacturing_order_id: float | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ManufacturingOrderRecipeRowListResponse]:
    """List all manufacturing order recipe rows

     Returns a list of manufacturing order recipe rows you've previously created. The manufacturing order
      recipe rows are returned in sorted order, with the most recent manufacturing order recipe rows
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        manufacturing_order_id (float | Unset):
        variant_id (int | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
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
        Response[ErrorResponse | ManufacturingOrderRecipeRowListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        manufacturing_order_id=manufacturing_order_id,
        variant_id=variant_id,
        ingredient_availability=ingredient_availability,
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
    manufacturing_order_id: float | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ManufacturingOrderRecipeRowListResponse | None:
    """List all manufacturing order recipe rows

     Returns a list of manufacturing order recipe rows you've previously created. The manufacturing order
      recipe rows are returned in sorted order, with the most recent manufacturing order recipe rows
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        manufacturing_order_id (float | Unset):
        variant_id (int | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
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
        ErrorResponse | ManufacturingOrderRecipeRowListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        manufacturing_order_id=manufacturing_order_id,
        variant_id=variant_id,
        ingredient_availability=ingredient_availability,
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
    manufacturing_order_id: float | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ManufacturingOrderRecipeRowListResponse]:
    """List all manufacturing order recipe rows

     Returns a list of manufacturing order recipe rows you've previously created. The manufacturing order
      recipe rows are returned in sorted order, with the most recent manufacturing order recipe rows
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        manufacturing_order_id (float | Unset):
        variant_id (int | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
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
        Response[ErrorResponse | ManufacturingOrderRecipeRowListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        manufacturing_order_id=manufacturing_order_id,
        variant_id=variant_id,
        ingredient_availability=ingredient_availability,
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
    manufacturing_order_id: float | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ManufacturingOrderRecipeRowListResponse | None:
    """List all manufacturing order recipe rows

     Returns a list of manufacturing order recipe rows you've previously created. The manufacturing order
      recipe rows are returned in sorted order, with the most recent manufacturing order recipe rows
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        manufacturing_order_id (float | Unset):
        variant_id (int | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
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
        ErrorResponse | ManufacturingOrderRecipeRowListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            manufacturing_order_id=manufacturing_order_id,
            variant_id=variant_id,
            ingredient_availability=ingredient_availability,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
