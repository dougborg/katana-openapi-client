from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_product_request import CreateProductRequest
from ...models.create_product_response_401 import CreateProductResponse401
from ...models.create_product_response_422 import CreateProductResponse422
from ...models.create_product_response_429 import CreateProductResponse429
from ...models.create_product_response_500 import CreateProductResponse500
from ...models.product import Product
from ...types import Response


def _get_kwargs(
    *,
    body: CreateProductRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/products",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
    | None
):
    if response.status_code == 200:
        response_200 = Product.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateProductResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateProductResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateProductResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateProductResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
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
    body: CreateProductRequest,
) -> Response[
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
]:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateProductResponse401, CreateProductResponse422, CreateProductResponse429, CreateProductResponse500, Product]]
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
    body: CreateProductRequest,
) -> (
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
    | None
):
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateProductResponse401, CreateProductResponse422, CreateProductResponse429, CreateProductResponse500, Product]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateProductRequest,
) -> Response[
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
]:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateProductResponse401, CreateProductResponse422, CreateProductResponse429, CreateProductResponse500, Product]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateProductRequest,
) -> (
    CreateProductResponse401
    | CreateProductResponse422
    | CreateProductResponse429
    | CreateProductResponse500
    | Product
    | None
):
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateProductResponse401, CreateProductResponse422, CreateProductResponse429, CreateProductResponse500, Product]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
