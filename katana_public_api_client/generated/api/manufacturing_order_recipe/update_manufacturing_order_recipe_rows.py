from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.manufacturing_order_recipe_row import ManufacturingOrderRecipeRow
from ...models.update_manufacturing_order_recipe_row_request import (
    UpdateManufacturingOrderRecipeRowRequest,
)
from ...models.update_manufacturing_order_recipe_rows_response_401 import (
    UpdateManufacturingOrderRecipeRowsResponse401,
)
from ...models.update_manufacturing_order_recipe_rows_response_429 import (
    UpdateManufacturingOrderRecipeRowsResponse429,
)
from ...models.update_manufacturing_order_recipe_rows_response_500 import (
    UpdateManufacturingOrderRecipeRowsResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_recipe_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderRecipeRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateManufacturingOrderRecipeRowsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = UpdateManufacturingOrderRecipeRowsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = UpdateManufacturingOrderRecipeRowsResponse500.from_dict(
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
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> Response[
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
]:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderRecipeRow, UpdateManufacturingOrderRecipeRowsResponse401, UpdateManufacturingOrderRecipeRowsResponse429, UpdateManufacturingOrderRecipeRowsResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> (
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
    | None
):
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderRecipeRow, UpdateManufacturingOrderRecipeRowsResponse401, UpdateManufacturingOrderRecipeRowsResponse429, UpdateManufacturingOrderRecipeRowsResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> Response[
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
]:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderRecipeRow, UpdateManufacturingOrderRecipeRowsResponse401, UpdateManufacturingOrderRecipeRowsResponse429, UpdateManufacturingOrderRecipeRowsResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> (
    ManufacturingOrderRecipeRow
    | UpdateManufacturingOrderRecipeRowsResponse401
    | UpdateManufacturingOrderRecipeRowsResponse429
    | UpdateManufacturingOrderRecipeRowsResponse500
    | None
):
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderRecipeRow, UpdateManufacturingOrderRecipeRowsResponse401, UpdateManufacturingOrderRecipeRowsResponse429, UpdateManufacturingOrderRecipeRowsResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
