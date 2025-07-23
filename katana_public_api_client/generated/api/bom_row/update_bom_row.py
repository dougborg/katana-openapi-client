from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.bom_row import BomRow
from ...models.update_bom_row_body import UpdateBomRowBody
from ...models.update_bom_row_response_401 import UpdateBomRowResponse401
from ...models.update_bom_row_response_404 import UpdateBomRowResponse404
from ...models.update_bom_row_response_422 import UpdateBomRowResponse422
from ...models.update_bom_row_response_429 import UpdateBomRowResponse429
from ...models.update_bom_row_response_500 import UpdateBomRowResponse500
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateBomRowBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/bom_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
    | None
):
    if response.status_code == 200:
        response_200 = BomRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateBomRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = UpdateBomRowResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 422:
        response_422 = UpdateBomRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdateBomRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateBomRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
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
    body: UpdateBomRowBody,
) -> Response[
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
]:
    """Update a BOM row

     Updates the specified BOM row by setting the values of the parameters passed. Any parameters not
    provided will be left unchanged.

    Args:
        id (int):
        body (UpdateBomRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BomRow, UpdateBomRowResponse401, UpdateBomRowResponse404, UpdateBomRowResponse422, UpdateBomRowResponse429, UpdateBomRowResponse500]]
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
    body: UpdateBomRowBody,
) -> (
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
    | None
):
    """Update a BOM row

     Updates the specified BOM row by setting the values of the parameters passed. Any parameters not
    provided will be left unchanged.

    Args:
        id (int):
        body (UpdateBomRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BomRow, UpdateBomRowResponse401, UpdateBomRowResponse404, UpdateBomRowResponse422, UpdateBomRowResponse429, UpdateBomRowResponse500]
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
    body: UpdateBomRowBody,
) -> Response[
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
]:
    """Update a BOM row

     Updates the specified BOM row by setting the values of the parameters passed. Any parameters not
    provided will be left unchanged.

    Args:
        id (int):
        body (UpdateBomRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BomRow, UpdateBomRowResponse401, UpdateBomRowResponse404, UpdateBomRowResponse422, UpdateBomRowResponse429, UpdateBomRowResponse500]]
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
    body: UpdateBomRowBody,
) -> (
    BomRow
    | UpdateBomRowResponse401
    | UpdateBomRowResponse404
    | UpdateBomRowResponse422
    | UpdateBomRowResponse429
    | UpdateBomRowResponse500
    | None
):
    """Update a BOM row

     Updates the specified BOM row by setting the values of the parameters passed. Any parameters not
    provided will be left unchanged.

    Args:
        id (int):
        body (UpdateBomRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BomRow, UpdateBomRowResponse401, UpdateBomRowResponse404, UpdateBomRowResponse422, UpdateBomRowResponse429, UpdateBomRowResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
