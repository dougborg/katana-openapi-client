from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.custom_fields_collection_list_response import (
    CustomFieldsCollectionListResponse,
)
from ...models.get_all_custom_fields_collections_response_401 import (
    GetAllCustomFieldsCollectionsResponse401,
)
from ...models.get_all_custom_fields_collections_response_429 import (
    GetAllCustomFieldsCollectionsResponse429,
)
from ...models.get_all_custom_fields_collections_response_500 import (
    GetAllCustomFieldsCollectionsResponse500,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/custom_fields_collections",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CustomFieldsCollectionListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllCustomFieldsCollectionsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetAllCustomFieldsCollectionsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetAllCustomFieldsCollectionsResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
]:
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomFieldsCollectionListResponse, GetAllCustomFieldsCollectionsResponse401, GetAllCustomFieldsCollectionsResponse429, GetAllCustomFieldsCollectionsResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
    | None
):
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomFieldsCollectionListResponse, GetAllCustomFieldsCollectionsResponse401, GetAllCustomFieldsCollectionsResponse429, GetAllCustomFieldsCollectionsResponse500]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
]:
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomFieldsCollectionListResponse, GetAllCustomFieldsCollectionsResponse401, GetAllCustomFieldsCollectionsResponse429, GetAllCustomFieldsCollectionsResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    CustomFieldsCollectionListResponse
    | GetAllCustomFieldsCollectionsResponse401
    | GetAllCustomFieldsCollectionsResponse429
    | GetAllCustomFieldsCollectionsResponse500
    | None
):
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomFieldsCollectionListResponse, GetAllCustomFieldsCollectionsResponse401, GetAllCustomFieldsCollectionsResponse429, GetAllCustomFieldsCollectionsResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
        )
    ).parsed
