from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response
from ...models.delete_serial_numbers_resource_type import (
    DeleteSerialNumbersResourceType,
)
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    resource_type: DeleteSerialNumbersResourceType,
    resource_id: int,
    serial_number_ids: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_resource_type = resource_type.value
    params["resource_type"] = json_resource_type

    params["resource_id"] = resource_id

    params["serial_number_ids"] = serial_number_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/serial_numbers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ErrorResponse | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400
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
) -> Response[Any | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    resource_type: DeleteSerialNumbersResourceType,
    resource_id: int,
    serial_number_ids: str,
) -> Response[Any | ErrorResponse]:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    Args:
        resource_type (DeleteSerialNumbersResourceType):
        resource_id (int):
        serial_number_ids (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        resource_type=resource_type,
        resource_id=resource_id,
        serial_number_ids=serial_number_ids,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    resource_type: DeleteSerialNumbersResourceType,
    resource_id: int,
    serial_number_ids: str,
) -> Any | ErrorResponse | None:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    Args:
        resource_type (DeleteSerialNumbersResourceType):
        resource_id (int):
        serial_number_ids (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        resource_type=resource_type,
        resource_id=resource_id,
        serial_number_ids=serial_number_ids,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    resource_type: DeleteSerialNumbersResourceType,
    resource_id: int,
    serial_number_ids: str,
) -> Response[Any | ErrorResponse]:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    Args:
        resource_type (DeleteSerialNumbersResourceType):
        resource_id (int):
        serial_number_ids (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        resource_type=resource_type,
        resource_id=resource_id,
        serial_number_ids=serial_number_ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    resource_type: DeleteSerialNumbersResourceType,
    resource_id: int,
    serial_number_ids: str,
) -> Any | ErrorResponse | None:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    Args:
        resource_type (DeleteSerialNumbersResourceType):
        resource_id (int):
        serial_number_ids (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            resource_type=resource_type,
            resource_id=resource_id,
            serial_number_ids=serial_number_ids,
        )
    ).parsed
