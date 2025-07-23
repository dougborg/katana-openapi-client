from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.bom_row import BomRow
from ...models.create_bom_row_request import CreateBomRowRequest
from ...models.create_bom_row_response_401 import CreateBomRowResponse401
from ...models.create_bom_row_response_422 import CreateBomRowResponse422
from ...models.create_bom_row_response_429 import CreateBomRowResponse429
from ...models.create_bom_row_response_500 import CreateBomRowResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: CreateBomRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/bom_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
    | None
):
    if response.status_code == 200:
        response_200 = BomRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateBomRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateBomRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateBomRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateBomRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
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
    body: CreateBomRowRequest,
) -> Response[
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
]:
    """Create a BOM row

     Create a new BOM row for a product.

    Args:
        body (CreateBomRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BomRow, CreateBomRowResponse401, CreateBomRowResponse422, CreateBomRowResponse429, CreateBomRowResponse500]]
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
    body: CreateBomRowRequest,
) -> (
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
    | None
):
    """Create a BOM row

     Create a new BOM row for a product.

    Args:
        body (CreateBomRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BomRow, CreateBomRowResponse401, CreateBomRowResponse422, CreateBomRowResponse429, CreateBomRowResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateBomRowRequest,
) -> Response[
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
]:
    """Create a BOM row

     Create a new BOM row for a product.

    Args:
        body (CreateBomRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BomRow, CreateBomRowResponse401, CreateBomRowResponse422, CreateBomRowResponse429, CreateBomRowResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateBomRowRequest,
) -> (
    BomRow
    | CreateBomRowResponse401
    | CreateBomRowResponse422
    | CreateBomRowResponse429
    | CreateBomRowResponse500
    | None
):
    """Create a BOM row

     Create a new BOM row for a product.

    Args:
        body (CreateBomRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BomRow, CreateBomRowResponse401, CreateBomRowResponse422, CreateBomRowResponse429, CreateBomRowResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
