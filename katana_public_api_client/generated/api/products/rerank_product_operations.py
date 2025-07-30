from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.product_operation_rerank import ProductOperationRerank
from ...models.product_operation_rerank_request import ProductOperationRerankRequest
from ...models.rerank_product_operations_response_400 import (
    RerankProductOperationsResponse400,
)
from ...models.rerank_product_operations_response_401 import (
    RerankProductOperationsResponse401,
)
from ...models.rerank_product_operations_response_429 import (
    RerankProductOperationsResponse429,
)
from ...models.rerank_product_operations_response_500 import (
    RerankProductOperationsResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ProductOperationRerankRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/product_operation_rerank",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ProductOperationRerank.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = RerankProductOperationsResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = RerankProductOperationsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = RerankProductOperationsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = RerankProductOperationsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
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
    body: ProductOperationRerankRequest,
) -> Response[
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
]:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ProductOperationRerank, RerankProductOperationsResponse400, RerankProductOperationsResponse401, RerankProductOperationsResponse429, RerankProductOperationsResponse500]]
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
    body: ProductOperationRerankRequest,
) -> (
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
    | None
):
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ProductOperationRerank, RerankProductOperationsResponse400, RerankProductOperationsResponse401, RerankProductOperationsResponse429, RerankProductOperationsResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> Response[
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
]:
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ProductOperationRerank, RerankProductOperationsResponse400, RerankProductOperationsResponse401, RerankProductOperationsResponse429, RerankProductOperationsResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ProductOperationRerankRequest,
) -> (
    ProductOperationRerank
    | RerankProductOperationsResponse400
    | RerankProductOperationsResponse401
    | RerankProductOperationsResponse429
    | RerankProductOperationsResponse500
    | None
):
    """Rerank product operations

     Reranks the operations for a product.

    Args:
        body (ProductOperationRerankRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ProductOperationRerank, RerankProductOperationsResponse400, RerankProductOperationsResponse401, RerankProductOperationsResponse429, RerankProductOperationsResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
