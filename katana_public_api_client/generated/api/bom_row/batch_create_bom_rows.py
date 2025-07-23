from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_create_bom_rows_request import BatchCreateBomRowsRequest
from ...models.batch_create_bom_rows_response_401 import BatchCreateBomRowsResponse401
from ...models.batch_create_bom_rows_response_422 import BatchCreateBomRowsResponse422
from ...models.batch_create_bom_rows_response_429 import BatchCreateBomRowsResponse429
from ...models.batch_create_bom_rows_response_500 import BatchCreateBomRowsResponse500
from ...models.bom_row_list_response import BomRowListResponse
from ...types import Response


def _get_kwargs(
    *,
    body: BatchCreateBomRowsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/bom_rows/batch/create",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = BomRowListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = BatchCreateBomRowsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = BatchCreateBomRowsResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = BatchCreateBomRowsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = BatchCreateBomRowsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
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
    body: BatchCreateBomRowsRequest,
) -> Response[
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
]:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchCreateBomRowsResponse401, BatchCreateBomRowsResponse422, BatchCreateBomRowsResponse429, BatchCreateBomRowsResponse500, BomRowListResponse]]
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
    body: BatchCreateBomRowsRequest,
) -> (
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
    | None
):
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchCreateBomRowsResponse401, BatchCreateBomRowsResponse422, BatchCreateBomRowsResponse429, BatchCreateBomRowsResponse500, BomRowListResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BatchCreateBomRowsRequest,
) -> Response[
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
]:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchCreateBomRowsResponse401, BatchCreateBomRowsResponse422, BatchCreateBomRowsResponse429, BatchCreateBomRowsResponse500, BomRowListResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BatchCreateBomRowsRequest,
) -> (
    BatchCreateBomRowsResponse401
    | BatchCreateBomRowsResponse422
    | BatchCreateBomRowsResponse429
    | BatchCreateBomRowsResponse500
    | BomRowListResponse
    | None
):
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchCreateBomRowsResponse401, BatchCreateBomRowsResponse422, BatchCreateBomRowsResponse429, BatchCreateBomRowsResponse500, BomRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
