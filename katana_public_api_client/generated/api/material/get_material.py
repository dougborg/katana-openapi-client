from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_material_extend_item import GetMaterialExtendItem
from ...models.get_material_response_401 import GetMaterialResponse401
from ...models.get_material_response_429 import GetMaterialResponse429
from ...models.get_material_response_500 import GetMaterialResponse500
from ...models.material import Material
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: int,
    *,
    extend: Unset | list[GetMaterialExtendItem] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/materials/{id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetMaterialResponse401
    | GetMaterialResponse429
    | GetMaterialResponse500
    | Material
    | None
):
    if response.status_code == 200:
        response_200 = Material.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetMaterialResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetMaterialResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetMaterialResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetMaterialResponse401 | GetMaterialResponse429 | GetMaterialResponse500 | Material
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
    extend: Unset | list[GetMaterialExtendItem] = UNSET,
) -> Response[
    GetMaterialResponse401 | GetMaterialResponse429 | GetMaterialResponse500 | Material
]:
    """Retrieve a material

     Retrieves the details of an existing material based on ID.

    Args:
        id (int):
        extend (Union[Unset, list[GetMaterialExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetMaterialResponse401, GetMaterialResponse429, GetMaterialResponse500, Material]]
    """

    kwargs = _get_kwargs(
        id=id,
        extend=extend,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetMaterialExtendItem] = UNSET,
) -> (
    GetMaterialResponse401
    | GetMaterialResponse429
    | GetMaterialResponse500
    | Material
    | None
):
    """Retrieve a material

     Retrieves the details of an existing material based on ID.

    Args:
        id (int):
        extend (Union[Unset, list[GetMaterialExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetMaterialResponse401, GetMaterialResponse429, GetMaterialResponse500, Material]
    """

    return sync_detailed(
        id=id,
        client=client,
        extend=extend,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetMaterialExtendItem] = UNSET,
) -> Response[
    GetMaterialResponse401 | GetMaterialResponse429 | GetMaterialResponse500 | Material
]:
    """Retrieve a material

     Retrieves the details of an existing material based on ID.

    Args:
        id (int):
        extend (Union[Unset, list[GetMaterialExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetMaterialResponse401, GetMaterialResponse429, GetMaterialResponse500, Material]]
    """

    kwargs = _get_kwargs(
        id=id,
        extend=extend,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetMaterialExtendItem] = UNSET,
) -> (
    GetMaterialResponse401
    | GetMaterialResponse429
    | GetMaterialResponse500
    | Material
    | None
):
    """Retrieve a material

     Retrieves the details of an existing material based on ID.

    Args:
        id (int):
        extend (Union[Unset, list[GetMaterialExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetMaterialResponse401, GetMaterialResponse429, GetMaterialResponse500, Material]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            extend=extend,
        )
    ).parsed
