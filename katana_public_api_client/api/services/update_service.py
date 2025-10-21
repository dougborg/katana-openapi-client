from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.service import Service
from ...models.update_service_request import UpdateServiceRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateServiceRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/services/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | Service | None:
    if response.status_code == 200:
        response_200 = Service.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | Service]:
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
    body: UpdateServiceRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Service]:
    """Update Service

     Update an existing Service. (See: [Update
    Service](https://developer.katanamrp.com/reference/updateservice))

    Args:
        id (int):
        body (UpdateServiceRequest): Request payload for updating an existing service's properties
            and specifications Example: {'name': 'Updated Assembly Service', 'uom': 'hours',
            'category_name': 'Professional Services', 'is_sellable': True, 'is_archived': False,
            'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Service]]
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
    body: UpdateServiceRequest,
) -> DetailedErrorResponse | ErrorResponse | Service | None:
    """Update Service

     Update an existing Service. (See: [Update
    Service](https://developer.katanamrp.com/reference/updateservice))

    Args:
        id (int):
        body (UpdateServiceRequest): Request payload for updating an existing service's properties
            and specifications Example: {'name': 'Updated Assembly Service', 'uom': 'hours',
            'category_name': 'Professional Services', 'is_sellable': True, 'is_archived': False,
            'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Service]
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
    body: UpdateServiceRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Service]:
    """Update Service

     Update an existing Service. (See: [Update
    Service](https://developer.katanamrp.com/reference/updateservice))

    Args:
        id (int):
        body (UpdateServiceRequest): Request payload for updating an existing service's properties
            and specifications Example: {'name': 'Updated Assembly Service', 'uom': 'hours',
            'category_name': 'Professional Services', 'is_sellable': True, 'is_archived': False,
            'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Service]]
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
    body: UpdateServiceRequest,
) -> DetailedErrorResponse | ErrorResponse | Service | None:
    """Update Service

     Update an existing Service. (See: [Update
    Service](https://developer.katanamrp.com/reference/updateservice))

    Args:
        id (int):
        body (UpdateServiceRequest): Request payload for updating an existing service's properties
            and specifications Example: {'name': 'Updated Assembly Service', 'uom': 'hours',
            'category_name': 'Professional Services', 'is_sellable': True, 'is_archived': False,
            'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Service]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
