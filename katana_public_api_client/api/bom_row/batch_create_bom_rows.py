from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.batch_create_bom_rows_request import BatchCreateBomRowsRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse


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
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = DetailedErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
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
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest): Request payload for creating multiple BOM rows in a
            single operation Example: {'bom_rows': [{'product_item_id': 3001, 'product_variant_id':
            2001, 'ingredient_variant_id': 2002, 'quantity': 2.5, 'notes': 'Primary component'},
            {'product_item_id': 3001, 'product_variant_id': 2001, 'ingredient_variant_id': 2003,
            'quantity': 1.0, 'notes': 'Secondary component'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DetailedErrorResponse, ErrorResponse]]
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
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest): Request payload for creating multiple BOM rows in a
            single operation Example: {'bom_rows': [{'product_item_id': 3001, 'product_variant_id':
            2001, 'ingredient_variant_id': 2002, 'quantity': 2.5, 'notes': 'Primary component'},
            {'product_item_id': 3001, 'product_variant_id': 2001, 'ingredient_variant_id': 2003,
            'quantity': 1.0, 'notes': 'Secondary component'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DetailedErrorResponse, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BatchCreateBomRowsRequest,
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest): Request payload for creating multiple BOM rows in a
            single operation Example: {'bom_rows': [{'product_item_id': 3001, 'product_variant_id':
            2001, 'ingredient_variant_id': 2002, 'quantity': 2.5, 'notes': 'Primary component'},
            {'product_item_id': 3001, 'product_variant_id': 2001, 'ingredient_variant_id': 2003,
            'quantity': 1.0, 'notes': 'Secondary component'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DetailedErrorResponse, ErrorResponse]]
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
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    """Create many BOM rows

     Create BOM rows for a product.

    Args:
        body (BatchCreateBomRowsRequest): Request payload for creating multiple BOM rows in a
            single operation Example: {'bom_rows': [{'product_item_id': 3001, 'product_variant_id':
            2001, 'ingredient_variant_id': 2002, 'quantity': 2.5, 'notes': 'Primary component'},
            {'product_item_id': 3001, 'product_variant_id': 2001, 'ingredient_variant_id': 2003,
            'quantity': 1.0, 'notes': 'Secondary component'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DetailedErrorResponse, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
