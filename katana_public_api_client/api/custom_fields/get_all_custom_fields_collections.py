from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.custom_fields_collection import CustomFieldsCollection
from ...models.custom_fields_collection_list_response import (
    CustomFieldsCollectionListResponse,
)
from ...models.error_response import ErrorResponse


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/custom_fields_collections",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CustomFieldsCollectionListResponse
    | list[CustomFieldsCollection]
    | ErrorResponse
    | None
):
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> CustomFieldsCollectionListResponse | list[CustomFieldsCollection]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                response_200_type_0 = []
                _response_200_type_0 = data
                for response_200_type_0_item_data in _response_200_type_0:
                    response_200_type_0_item = CustomFieldsCollection.from_dict(
                        cast(Mapping[str, Any], response_200_type_0_item_data)
                    )

                    response_200_type_0.append(response_200_type_0_item)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = CustomFieldsCollectionListResponse.from_dict(
                cast(Mapping[str, Any], data)
            )

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

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
) -> Response[
    CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse
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
) -> Response[
    CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse
]:
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> (
    CustomFieldsCollectionListResponse
    | list[CustomFieldsCollection]
    | ErrorResponse
    | None
):
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse
]:
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    CustomFieldsCollectionListResponse
    | list[CustomFieldsCollection]
    | ErrorResponse
    | None
):
    """List all custom fields collections

     Retrieves a list of custom fields collections.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomFieldsCollectionListResponse | list[CustomFieldsCollection] | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
