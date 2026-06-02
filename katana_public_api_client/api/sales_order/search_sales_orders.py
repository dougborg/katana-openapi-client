from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_order_list_response import SalesOrderListResponse
from ...models.sales_order_search_request import SalesOrderSearchRequest


def _get_kwargs(
    *,
    body: SalesOrderSearchRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_orders/search",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesOrderListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SalesOrderSearchRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderListResponse]:
    """Search sales orders

     Searches sales orders using a structured filter body with nested
    logical operators (``and`` / ``or``) and per-field comparators.
    Only the fields in the request schema may appear in ``where`` /
    ``order``; unknown fields return 422. Custom field values are
    addressable via ``custom_fields.<uuid>`` nested paths. Returns the
    same shape as ``GET /sales_orders`` — a paginated list of
    ``SalesOrder`` records.

    Args:
        body (SalesOrderSearchRequest): Structured filter body for ``POST /sales_orders/search``.
            Returns
            the same paginated ``{"data": [...]}`` shape as
            ``GET /sales_orders`` plus an ``X-Pagination`` header. Beta —
            request/response shape may evolve before GA.
             Example: {'filter': {'where': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}},
            {'created_at': {'gte': '2026-01-01T00:00:00.000Z'}},
            {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at DESC',
            'id DESC'], 'limit': 50, 'page': 1}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesOrderListResponse]
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
    body: SalesOrderSearchRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderListResponse | None:
    """Search sales orders

     Searches sales orders using a structured filter body with nested
    logical operators (``and`` / ``or``) and per-field comparators.
    Only the fields in the request schema may appear in ``where`` /
    ``order``; unknown fields return 422. Custom field values are
    addressable via ``custom_fields.<uuid>`` nested paths. Returns the
    same shape as ``GET /sales_orders`` — a paginated list of
    ``SalesOrder`` records.

    Args:
        body (SalesOrderSearchRequest): Structured filter body for ``POST /sales_orders/search``.
            Returns
            the same paginated ``{"data": [...]}`` shape as
            ``GET /sales_orders`` plus an ``X-Pagination`` header. Beta —
            request/response shape may evolve before GA.
             Example: {'filter': {'where': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}},
            {'created_at': {'gte': '2026-01-01T00:00:00.000Z'}},
            {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at DESC',
            'id DESC'], 'limit': 50, 'page': 1}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesOrderListResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SalesOrderSearchRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderListResponse]:
    """Search sales orders

     Searches sales orders using a structured filter body with nested
    logical operators (``and`` / ``or``) and per-field comparators.
    Only the fields in the request schema may appear in ``where`` /
    ``order``; unknown fields return 422. Custom field values are
    addressable via ``custom_fields.<uuid>`` nested paths. Returns the
    same shape as ``GET /sales_orders`` — a paginated list of
    ``SalesOrder`` records.

    Args:
        body (SalesOrderSearchRequest): Structured filter body for ``POST /sales_orders/search``.
            Returns
            the same paginated ``{"data": [...]}`` shape as
            ``GET /sales_orders`` plus an ``X-Pagination`` header. Beta —
            request/response shape may evolve before GA.
             Example: {'filter': {'where': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}},
            {'created_at': {'gte': '2026-01-01T00:00:00.000Z'}},
            {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at DESC',
            'id DESC'], 'limit': 50, 'page': 1}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesOrderListResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SalesOrderSearchRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderListResponse | None:
    """Search sales orders

     Searches sales orders using a structured filter body with nested
    logical operators (``and`` / ``or``) and per-field comparators.
    Only the fields in the request schema may appear in ``where`` /
    ``order``; unknown fields return 422. Custom field values are
    addressable via ``custom_fields.<uuid>`` nested paths. Returns the
    same shape as ``GET /sales_orders`` — a paginated list of
    ``SalesOrder`` records.

    Args:
        body (SalesOrderSearchRequest): Structured filter body for ``POST /sales_orders/search``.
            Returns
            the same paginated ``{"data": [...]}`` shape as
            ``GET /sales_orders`` plus an ``X-Pagination`` header. Beta —
            request/response shape may evolve before GA.
             Example: {'filter': {'where': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}},
            {'created_at': {'gte': '2026-01-01T00:00:00.000Z'}},
            {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at DESC',
            'id DESC'], 'limit': 50, 'page': 1}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesOrderListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
