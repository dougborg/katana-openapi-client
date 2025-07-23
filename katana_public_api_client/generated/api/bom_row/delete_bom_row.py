from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_bom_row_response_401 import DeleteBomRowResponse401
from ...models.delete_bom_row_response_404 import DeleteBomRowResponse404
from ...models.delete_bom_row_response_429 import DeleteBomRowResponse429
from ...models.delete_bom_row_response_500 import DeleteBomRowResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/bom_rows/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = DeleteBomRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteBomRowResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteBomRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteBomRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
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
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
]:
    """Delete a BOM row

     Deletes a BOM row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteBomRowResponse401, DeleteBomRowResponse404, DeleteBomRowResponse429, DeleteBomRowResponse500]]
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
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
    | None
):
    """Delete a BOM row

     Deletes a BOM row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteBomRowResponse401, DeleteBomRowResponse404, DeleteBomRowResponse429, DeleteBomRowResponse500]
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
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
]:
    """Delete a BOM row

     Deletes a BOM row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteBomRowResponse401, DeleteBomRowResponse404, DeleteBomRowResponse429, DeleteBomRowResponse500]]
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
    Any
    | DeleteBomRowResponse401
    | DeleteBomRowResponse404
    | DeleteBomRowResponse429
    | DeleteBomRowResponse500
    | None
):
    """Delete a BOM row

     Deletes a BOM row by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteBomRowResponse401, DeleteBomRowResponse404, DeleteBomRowResponse429, DeleteBomRowResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
