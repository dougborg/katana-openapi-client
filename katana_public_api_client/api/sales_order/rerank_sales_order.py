from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.rerank_orders_response import RerankOrdersResponse
from ...models.rerank_sales_order_request import RerankSalesOrderRequest


def _get_kwargs(
    *,
    body: RerankSalesOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_order_rerank",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse | None:
    if response.status_code == 200:
        response_200 = RerankOrdersResponse.from_dict(response.json())

        return response_200

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RerankSalesOrderRequest,
) -> Response[Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse]:
    """Change a sales order's rank

     Moves one or more sales orders to an exact place in the sales order list.

    The sales orders in `order_ids` are placed as one consecutive block, in the order given, at the
    place set in `place`. The first id ends up highest in the list. All other sales orders keep their
    order relative to each other.

    `before_id` places them directly above that sales order, and `after_id` directly below it. Sending
    the same request again changes nothing, so a request can be retried safely.

    Only open sales orders can be reranked. A sales order moves together with its linked manufacturing
    orders.

    To rerank more than 250 sales orders, send them in batches: the first batch with `place.position`
    set to `top`, each next batch with `place.after_id` set to the last id in the previous response's
    `order_ids`.

    Sales order lists show the new order shortly after the request returns.

    The request returns 422 when any of the sales orders, including the one in `before_id` or
    `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.

    Args:
        body (RerankSalesOrderRequest): Request payload for repositioning a sales order in the
            schedule, relative to another sales order Example: {'order_ids': [1], 'place':
            {'before_id': 4}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse]
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
    body: RerankSalesOrderRequest,
) -> Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse | None:
    """Change a sales order's rank

     Moves one or more sales orders to an exact place in the sales order list.

    The sales orders in `order_ids` are placed as one consecutive block, in the order given, at the
    place set in `place`. The first id ends up highest in the list. All other sales orders keep their
    order relative to each other.

    `before_id` places them directly above that sales order, and `after_id` directly below it. Sending
    the same request again changes nothing, so a request can be retried safely.

    Only open sales orders can be reranked. A sales order moves together with its linked manufacturing
    orders.

    To rerank more than 250 sales orders, send them in batches: the first batch with `place.position`
    set to `top`, each next batch with `place.after_id` set to the last id in the previous response's
    `order_ids`.

    Sales order lists show the new order shortly after the request returns.

    The request returns 422 when any of the sales orders, including the one in `before_id` or
    `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.

    Args:
        body (RerankSalesOrderRequest): Request payload for repositioning a sales order in the
            schedule, relative to another sales order Example: {'order_ids': [1], 'place':
            {'before_id': 4}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RerankSalesOrderRequest,
) -> Response[Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse]:
    """Change a sales order's rank

     Moves one or more sales orders to an exact place in the sales order list.

    The sales orders in `order_ids` are placed as one consecutive block, in the order given, at the
    place set in `place`. The first id ends up highest in the list. All other sales orders keep their
    order relative to each other.

    `before_id` places them directly above that sales order, and `after_id` directly below it. Sending
    the same request again changes nothing, so a request can be retried safely.

    Only open sales orders can be reranked. A sales order moves together with its linked manufacturing
    orders.

    To rerank more than 250 sales orders, send them in batches: the first batch with `place.position`
    set to `top`, each next batch with `place.after_id` set to the last id in the previous response's
    `order_ids`.

    Sales order lists show the new order shortly after the request returns.

    The request returns 422 when any of the sales orders, including the one in `before_id` or
    `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.

    Args:
        body (RerankSalesOrderRequest): Request payload for repositioning a sales order in the
            schedule, relative to another sales order Example: {'order_ids': [1], 'place':
            {'before_id': 4}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RerankSalesOrderRequest,
) -> Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse | None:
    """Change a sales order's rank

     Moves one or more sales orders to an exact place in the sales order list.

    The sales orders in `order_ids` are placed as one consecutive block, in the order given, at the
    place set in `place`. The first id ends up highest in the list. All other sales orders keep their
    order relative to each other.

    `before_id` places them directly above that sales order, and `after_id` directly below it. Sending
    the same request again changes nothing, so a request can be retried safely.

    Only open sales orders can be reranked. A sales order moves together with its linked manufacturing
    orders.

    To rerank more than 250 sales orders, send them in batches: the first batch with `place.position`
    set to `top`, each next batch with `place.after_id` set to the last id in the previous response's
    `order_ids`.

    Sales order lists show the new order shortly after the request returns.

    The request returns 422 when any of the sales orders, including the one in `before_id` or
    `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.

    Args:
        body (RerankSalesOrderRequest): Request payload for repositioning a sales order in the
            schedule, relative to another sales order Example: {'order_ids': [1], 'place':
            {'before_id': 4}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | DetailedErrorResponse | ErrorResponse | RerankOrdersResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
