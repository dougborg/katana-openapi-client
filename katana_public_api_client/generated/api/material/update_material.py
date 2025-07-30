from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.material import Material
from ...models.update_material_request import UpdateMaterialRequest
from ...models.update_material_response_401 import UpdateMaterialResponse401
from ...models.update_material_response_422 import UpdateMaterialResponse422
from ...models.update_material_response_429 import UpdateMaterialResponse429
from ...models.update_material_response_500 import UpdateMaterialResponse500
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateMaterialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/materials/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
    | None
):
    if response.status_code == 200:
        response_200 = Material.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateMaterialResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = UpdateMaterialResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdateMaterialResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateMaterialResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
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
    body: UpdateMaterialRequest,
) -> Response[
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
]:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Material, UpdateMaterialResponse401, UpdateMaterialResponse422, UpdateMaterialResponse429, UpdateMaterialResponse500]]
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
    body: UpdateMaterialRequest,
) -> (
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
    | None
):
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Material, UpdateMaterialResponse401, UpdateMaterialResponse422, UpdateMaterialResponse429, UpdateMaterialResponse500]
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
    body: UpdateMaterialRequest,
) -> Response[
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
]:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Material, UpdateMaterialResponse401, UpdateMaterialResponse422, UpdateMaterialResponse429, UpdateMaterialResponse500]]
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
    body: UpdateMaterialRequest,
) -> (
    Material
    | UpdateMaterialResponse401
    | UpdateMaterialResponse422
    | UpdateMaterialResponse429
    | UpdateMaterialResponse500
    | None
):
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Material, UpdateMaterialResponse401, UpdateMaterialResponse422, UpdateMaterialResponse429, UpdateMaterialResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
