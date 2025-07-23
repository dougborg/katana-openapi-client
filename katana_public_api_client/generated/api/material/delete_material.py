from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_material_response_204 import DeleteMaterialResponse204
from ...models.delete_material_response_401 import DeleteMaterialResponse401
from ...models.delete_material_response_404 import DeleteMaterialResponse404
from ...models.delete_material_response_429 import DeleteMaterialResponse429
from ...models.delete_material_response_500 import DeleteMaterialResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/materials/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
    | None
):
    if response.status_code == 204:
        response_204 = DeleteMaterialResponse204.from_dict(response.json())

        return response_204
    if response.status_code == 401:
        response_401 = DeleteMaterialResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteMaterialResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteMaterialResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteMaterialResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
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
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
]:
    """Delete a material

     Deletes a material by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DeleteMaterialResponse204, DeleteMaterialResponse401, DeleteMaterialResponse404, DeleteMaterialResponse429, DeleteMaterialResponse500]]
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
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
    | None
):
    """Delete a material

     Deletes a material by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DeleteMaterialResponse204, DeleteMaterialResponse401, DeleteMaterialResponse404, DeleteMaterialResponse429, DeleteMaterialResponse500]
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
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
]:
    """Delete a material

     Deletes a material by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DeleteMaterialResponse204, DeleteMaterialResponse401, DeleteMaterialResponse404, DeleteMaterialResponse429, DeleteMaterialResponse500]]
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
    DeleteMaterialResponse204
    | DeleteMaterialResponse401
    | DeleteMaterialResponse404
    | DeleteMaterialResponse429
    | DeleteMaterialResponse500
    | None
):
    """Delete a material

     Deletes a material by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DeleteMaterialResponse204, DeleteMaterialResponse401, DeleteMaterialResponse404, DeleteMaterialResponse429, DeleteMaterialResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
