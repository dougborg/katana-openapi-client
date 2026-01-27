from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.deletable_entity import DeletableEntity
from ...models.error_response import ErrorResponse
from ...models.location_type_0 import LocationType0


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/locations/{id}".format(
            id=quote(str(id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeletableEntity | LocationType0 | ErrorResponse | None:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> DeletableEntity | LocationType0:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_location_type_0 = LocationType0.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_location_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_location_type_1 = DeletableEntity.from_dict(
                cast(Mapping[str, Any], data)
            )

            return componentsschemas_location_type_1

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[DeletableEntity | LocationType0 | ErrorResponse]:
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
) -> Response[DeletableEntity | LocationType0 | ErrorResponse]:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DeletableEntity | LocationType0 | ErrorResponse]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> DeletableEntity | LocationType0 | ErrorResponse | None:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DeletableEntity | LocationType0 | ErrorResponse
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DeletableEntity | LocationType0 | ErrorResponse]:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DeletableEntity | LocationType0 | ErrorResponse]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> DeletableEntity | LocationType0 | ErrorResponse | None:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DeletableEntity | LocationType0 | ErrorResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
