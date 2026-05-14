from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_order_row_list_response import SalesOrderRowListResponse
from ...models.search_filter_request import SearchFilterRequest


def _get_kwargs(
    *,
    body: SearchFilterRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_order_rows/search",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderRowListResponse.from_dict(response.json())

        return response_200

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SearchFilterRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse]:
    """Search sales order rows

     Search sales order rows using a LoopBack-style filter body. Unlike
    ``GET /sales_order_rows`` (which uses simple query parameters), this
    endpoint accepts a rich ``filter`` object with comparison operators,
    boolean composition, and explicit pagination.

    Args:
        body (SearchFilterRequest): LoopBack-style filter envelope used by POST search endpoints.
            The
            ``filter`` body supports pagination (``limit`` / ``page`` / ``skip``),
            ordering, and a ``where`` clause with comparison operators
            (``eq`` / ``neq`` / ``gt`` / ``gte`` / ``lt`` / ``lte`` / ``like`` /
            ``ilike`` / ``inq`` / ``nin`` / ``between`` / ``regexp`` / ``exists``)
            plus ``and`` / ``or`` composition. Where clause values are
            intentionally left as free-form because Katana's filter grammar is
            the same regardless of which field is being filtered. Example: {'filter': {'limit': 50,
            'where': {'sales_order_id': {'inq': [1, 2, 3]}}, 'order': 'created_at DESC'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse]
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
    body: SearchFilterRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse | None:
    """Search sales order rows

     Search sales order rows using a LoopBack-style filter body. Unlike
    ``GET /sales_order_rows`` (which uses simple query parameters), this
    endpoint accepts a rich ``filter`` object with comparison operators,
    boolean composition, and explicit pagination.

    Args:
        body (SearchFilterRequest): LoopBack-style filter envelope used by POST search endpoints.
            The
            ``filter`` body supports pagination (``limit`` / ``page`` / ``skip``),
            ordering, and a ``where`` clause with comparison operators
            (``eq`` / ``neq`` / ``gt`` / ``gte`` / ``lt`` / ``lte`` / ``like`` /
            ``ilike`` / ``inq`` / ``nin`` / ``between`` / ``regexp`` / ``exists``)
            plus ``and`` / ``or`` composition. Where clause values are
            intentionally left as free-form because Katana's filter grammar is
            the same regardless of which field is being filtered. Example: {'filter': {'limit': 50,
            'where': {'sales_order_id': {'inq': [1, 2, 3]}}, 'order': 'created_at DESC'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SearchFilterRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse]:
    """Search sales order rows

     Search sales order rows using a LoopBack-style filter body. Unlike
    ``GET /sales_order_rows`` (which uses simple query parameters), this
    endpoint accepts a rich ``filter`` object with comparison operators,
    boolean composition, and explicit pagination.

    Args:
        body (SearchFilterRequest): LoopBack-style filter envelope used by POST search endpoints.
            The
            ``filter`` body supports pagination (``limit`` / ``page`` / ``skip``),
            ordering, and a ``where`` clause with comparison operators
            (``eq`` / ``neq`` / ``gt`` / ``gte`` / ``lt`` / ``lte`` / ``like`` /
            ``ilike`` / ``inq`` / ``nin`` / ``between`` / ``regexp`` / ``exists``)
            plus ``and`` / ``or`` composition. Where clause values are
            intentionally left as free-form because Katana's filter grammar is
            the same regardless of which field is being filtered. Example: {'filter': {'limit': 50,
            'where': {'sales_order_id': {'inq': [1, 2, 3]}}, 'order': 'created_at DESC'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SearchFilterRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse | None:
    """Search sales order rows

     Search sales order rows using a LoopBack-style filter body. Unlike
    ``GET /sales_order_rows`` (which uses simple query parameters), this
    endpoint accepts a rich ``filter`` object with comparison operators,
    boolean composition, and explicit pagination.

    Args:
        body (SearchFilterRequest): LoopBack-style filter envelope used by POST search endpoints.
            The
            ``filter`` body supports pagination (``limit`` / ``page`` / ``skip``),
            ordering, and a ``where`` clause with comparison operators
            (``eq`` / ``neq`` / ``gt`` / ``gte`` / ``lt`` / ``lte`` / ``like`` /
            ``ilike`` / ``inq`` / ``nin`` / ``between`` / ``regexp`` / ``exists``)
            plus ``and`` / ``or`` composition. Where clause values are
            intentionally left as free-form because Katana's filter grammar is
            the same regardless of which field is being filtered. Example: {'filter': {'limit': 50,
            'where': {'sales_order_id': {'inq': [1, 2, 3]}}, 'order': 'created_at DESC'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesOrderRowListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
