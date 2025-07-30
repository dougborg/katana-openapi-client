from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_variant_request import CreateVariantRequest
from ...models.create_variant_response_401 import CreateVariantResponse401
from ...models.create_variant_response_422 import CreateVariantResponse422
from ...models.create_variant_response_429 import CreateVariantResponse429
from ...models.create_variant_response_500 import CreateVariantResponse500
from ...models.variant import Variant
from ...types import Response


def _get_kwargs(
    *,
    body: CreateVariantRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/variants",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
    | None
):
    if response.status_code == 200:
        response_200 = Variant.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateVariantResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateVariantResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateVariantResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateVariantResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
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
    body: CreateVariantRequest,
) -> Response[
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
]:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateVariantResponse401, CreateVariantResponse422, CreateVariantResponse429, CreateVariantResponse500, Variant]]
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
    body: CreateVariantRequest,
) -> (
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
    | None
):
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateVariantResponse401, CreateVariantResponse422, CreateVariantResponse429, CreateVariantResponse500, Variant]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVariantRequest,
) -> Response[
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
]:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateVariantResponse401, CreateVariantResponse422, CreateVariantResponse429, CreateVariantResponse500, Variant]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVariantRequest,
) -> (
    CreateVariantResponse401
    | CreateVariantResponse422
    | CreateVariantResponse429
    | CreateVariantResponse500
    | Variant
    | None
):
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateVariantResponse401, CreateVariantResponse422, CreateVariantResponse429, CreateVariantResponse500, Variant]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
