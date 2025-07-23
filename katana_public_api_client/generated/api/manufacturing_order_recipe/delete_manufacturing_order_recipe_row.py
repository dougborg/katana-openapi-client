from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_manufacturing_order_recipe_row_response_204 import (
    DeleteManufacturingOrderRecipeRowResponse204,
)
from ...models.delete_manufacturing_order_recipe_row_response_401 import (
    DeleteManufacturingOrderRecipeRowResponse401,
)
from ...models.delete_manufacturing_order_recipe_row_response_404 import (
    DeleteManufacturingOrderRecipeRowResponse404,
)
from ...models.delete_manufacturing_order_recipe_row_response_429 import (
    DeleteManufacturingOrderRecipeRowResponse429,
)
from ...models.delete_manufacturing_order_recipe_row_response_500 import (
    DeleteManufacturingOrderRecipeRowResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/manufacturing_order_recipe_rows/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
    | None
):
    if response.status_code == 204:
        response_204 = DeleteManufacturingOrderRecipeRowResponse204.from_dict(
            response.json()
        )

        return response_204
    if response.status_code == 401:
        response_401 = DeleteManufacturingOrderRecipeRowResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 404:
        response_404 = DeleteManufacturingOrderRecipeRowResponse404.from_dict(
            response.json()
        )

        return response_404
    if response.status_code == 429:
        response_429 = DeleteManufacturingOrderRecipeRowResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = DeleteManufacturingOrderRecipeRowResponse500.from_dict(
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
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
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
) -> Response[
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
]:
    """Delete a manufacturing order recipe row

     Deletes a single manufacturing order recipe row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DeleteManufacturingOrderRecipeRowResponse204, DeleteManufacturingOrderRecipeRowResponse401, DeleteManufacturingOrderRecipeRowResponse404, DeleteManufacturingOrderRecipeRowResponse429, DeleteManufacturingOrderRecipeRowResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
    | None
):
    """Delete a manufacturing order recipe row

     Deletes a single manufacturing order recipe row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DeleteManufacturingOrderRecipeRowResponse204, DeleteManufacturingOrderRecipeRowResponse401, DeleteManufacturingOrderRecipeRowResponse404, DeleteManufacturingOrderRecipeRowResponse429, DeleteManufacturingOrderRecipeRowResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
]:
    """Delete a manufacturing order recipe row

     Deletes a single manufacturing order recipe row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DeleteManufacturingOrderRecipeRowResponse204, DeleteManufacturingOrderRecipeRowResponse401, DeleteManufacturingOrderRecipeRowResponse404, DeleteManufacturingOrderRecipeRowResponse429, DeleteManufacturingOrderRecipeRowResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteManufacturingOrderRecipeRowResponse204
    | DeleteManufacturingOrderRecipeRowResponse401
    | DeleteManufacturingOrderRecipeRowResponse404
    | DeleteManufacturingOrderRecipeRowResponse429
    | DeleteManufacturingOrderRecipeRowResponse500
    | None
):
    """Delete a manufacturing order recipe row

     Deletes a single manufacturing order recipe row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DeleteManufacturingOrderRecipeRowResponse204, DeleteManufacturingOrderRecipeRowResponse401, DeleteManufacturingOrderRecipeRowResponse404, DeleteManufacturingOrderRecipeRowResponse429, DeleteManufacturingOrderRecipeRowResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
