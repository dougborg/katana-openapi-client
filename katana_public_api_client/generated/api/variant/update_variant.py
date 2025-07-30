from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_variant_request import UpdateVariantRequest
from ...models.update_variant_response_401 import UpdateVariantResponse401
from ...models.update_variant_response_422 import UpdateVariantResponse422
from ...models.update_variant_response_429 import UpdateVariantResponse429
from ...models.update_variant_response_500 import UpdateVariantResponse500
from ...models.variant import Variant
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateVariantRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/variants/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
    | None
):
    if response.status_code == 200:
        response_200 = Variant.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateVariantResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = UpdateVariantResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdateVariantResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateVariantResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
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
    body: UpdateVariantRequest,
) -> Response[
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
]:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[UpdateVariantResponse401, UpdateVariantResponse422, UpdateVariantResponse429, UpdateVariantResponse500, Variant]]
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
    body: UpdateVariantRequest,
) -> (
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
    | None
):
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[UpdateVariantResponse401, UpdateVariantResponse422, UpdateVariantResponse429, UpdateVariantResponse500, Variant]
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
    body: UpdateVariantRequest,
) -> Response[
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
]:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[UpdateVariantResponse401, UpdateVariantResponse422, UpdateVariantResponse429, UpdateVariantResponse500, Variant]]
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
    body: UpdateVariantRequest,
) -> (
    UpdateVariantResponse401
    | UpdateVariantResponse422
    | UpdateVariantResponse429
    | UpdateVariantResponse500
    | Variant
    | None
):
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[UpdateVariantResponse401, UpdateVariantResponse422, UpdateVariantResponse429, UpdateVariantResponse500, Variant]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
