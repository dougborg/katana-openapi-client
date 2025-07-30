from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_recipe_row_request import (
    CreateManufacturingOrderRecipeRowRequest,
)
from ...models.create_manufacturing_order_recipe_rows_response_401 import (
    CreateManufacturingOrderRecipeRowsResponse401,
)
from ...models.create_manufacturing_order_recipe_rows_response_429 import (
    CreateManufacturingOrderRecipeRowsResponse429,
)
from ...models.create_manufacturing_order_recipe_rows_response_500 import (
    CreateManufacturingOrderRecipeRowsResponse500,
)
from ...models.manufacturing_order_recipe_row import ManufacturingOrderRecipeRow
from ...types import Response


def _get_kwargs(
    *,
    body: CreateManufacturingOrderRecipeRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_recipe_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderRecipeRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateManufacturingOrderRecipeRowsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = CreateManufacturingOrderRecipeRowsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = CreateManufacturingOrderRecipeRowsResponse500.from_dict(
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
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
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
    body: CreateManufacturingOrderRecipeRowRequest,
) -> Response[
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
]:
    """Create a manufacturing order recipe row

     Add a recipe row to an existing manufacturing order.
      Recipe rows cannot be added when the manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderRecipeRowsResponse401, CreateManufacturingOrderRecipeRowsResponse429, CreateManufacturingOrderRecipeRowsResponse500, ManufacturingOrderRecipeRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRecipeRowRequest,
) -> (
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    """Create a manufacturing order recipe row

     Add a recipe row to an existing manufacturing order.
      Recipe rows cannot be added when the manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderRecipeRowsResponse401, CreateManufacturingOrderRecipeRowsResponse429, CreateManufacturingOrderRecipeRowsResponse500, ManufacturingOrderRecipeRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRecipeRowRequest,
) -> Response[
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
]:
    """Create a manufacturing order recipe row

     Add a recipe row to an existing manufacturing order.
      Recipe rows cannot be added when the manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderRecipeRowsResponse401, CreateManufacturingOrderRecipeRowsResponse429, CreateManufacturingOrderRecipeRowsResponse500, ManufacturingOrderRecipeRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRecipeRowRequest,
) -> (
    CreateManufacturingOrderRecipeRowsResponse401
    | CreateManufacturingOrderRecipeRowsResponse429
    | CreateManufacturingOrderRecipeRowsResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    """Create a manufacturing order recipe row

     Add a recipe row to an existing manufacturing order.
      Recipe rows cannot be added when the manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderRecipeRowsResponse401, CreateManufacturingOrderRecipeRowsResponse429, CreateManufacturingOrderRecipeRowsResponse500, ManufacturingOrderRecipeRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
