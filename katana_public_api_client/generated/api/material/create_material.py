from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_material_request import CreateMaterialRequest
from ...models.create_material_response_401 import CreateMaterialResponse401
from ...models.create_material_response_422 import CreateMaterialResponse422
from ...models.create_material_response_429 import CreateMaterialResponse429
from ...models.create_material_response_500 import CreateMaterialResponse500
from ...models.material import Material
from ...types import Response


def _get_kwargs(
    *,
    body: CreateMaterialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/materials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
    | None
):
    if response.status_code == 200:
        response_200 = Material.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateMaterialResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateMaterialResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateMaterialResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateMaterialResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
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
    body: CreateMaterialRequest,
) -> Response[
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
]:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateMaterialResponse401, CreateMaterialResponse422, CreateMaterialResponse429, CreateMaterialResponse500, Material]]
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
    body: CreateMaterialRequest,
) -> (
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
    | None
):
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateMaterialResponse401, CreateMaterialResponse422, CreateMaterialResponse429, CreateMaterialResponse500, Material]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMaterialRequest,
) -> Response[
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
]:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateMaterialResponse401, CreateMaterialResponse422, CreateMaterialResponse429, CreateMaterialResponse500, Material]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMaterialRequest,
) -> (
    CreateMaterialResponse401
    | CreateMaterialResponse422
    | CreateMaterialResponse429
    | CreateMaterialResponse500
    | Material
    | None
):
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateMaterialResponse401, CreateMaterialResponse422, CreateMaterialResponse429, CreateMaterialResponse500, Material]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
