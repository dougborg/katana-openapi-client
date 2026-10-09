from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.create_service_request import CreateServiceRequest
from ...models.create_service_x_custom_fields_format import (
    CreateServiceXCustomFieldsFormat,
)
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.service import Service


def _get_kwargs(
    *,
    body: CreateServiceRequest,
    x_custom_fields_format: CreateServiceXCustomFieldsFormat | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_custom_fields_format, Unset):
        headers["X-Custom-Fields-Format"] = str(x_custom_fields_format)

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services",
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
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceRequest,
    x_custom_fields_format: CreateServiceXCustomFieldsFormat | Unset = UNSET,
) -> Response[DetailedErrorResponse | ErrorResponse | Service]:
    """Create Service

     Create a new Service. (See: [Create
    Service](https://developer.katanamrp.com/reference/createservice))

    Args:
        x_custom_fields_format (CreateServiceXCustomFieldsFormat | Unset):
        body (CreateServiceRequest): Request payload for creating a new service with variants and
            specifications Example: {'name': 'Assembly Service', 'uom': 'hours', 'category_name':
            'Manufacturing Services', 'additional_info': 'Professional product assembly service',
            'is_sellable': True, 'custom_field_collection_id': 1, 'variants': [{'sku': 'ASSM-001',
            'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | Service]
    """

    kwargs = _get_kwargs(
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceRequest,
    x_custom_fields_format: CreateServiceXCustomFieldsFormat | Unset = UNSET,
) -> DetailedErrorResponse | ErrorResponse | Service | None:
    """Create Service

     Create a new Service. (See: [Create
    Service](https://developer.katanamrp.com/reference/createservice))

    Args:
        x_custom_fields_format (CreateServiceXCustomFieldsFormat | Unset):
        body (CreateServiceRequest): Request payload for creating a new service with variants and
            specifications Example: {'name': 'Assembly Service', 'uom': 'hours', 'category_name':
            'Manufacturing Services', 'additional_info': 'Professional product assembly service',
            'is_sellable': True, 'custom_field_collection_id': 1, 'variants': [{'sku': 'ASSM-001',
            'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | Service
    """

    return sync_detailed(
        client=client,
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceRequest,
    x_custom_fields_format: CreateServiceXCustomFieldsFormat | Unset = UNSET,
) -> Response[DetailedErrorResponse | ErrorResponse | Service]:
    """Create Service

     Create a new Service. (See: [Create
    Service](https://developer.katanamrp.com/reference/createservice))

    Args:
        x_custom_fields_format (CreateServiceXCustomFieldsFormat | Unset):
        body (CreateServiceRequest): Request payload for creating a new service with variants and
            specifications Example: {'name': 'Assembly Service', 'uom': 'hours', 'category_name':
            'Manufacturing Services', 'additional_info': 'Professional product assembly service',
            'is_sellable': True, 'custom_field_collection_id': 1, 'variants': [{'sku': 'ASSM-001',
            'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | Service]
    """

    kwargs = _get_kwargs(
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceRequest,
    x_custom_fields_format: CreateServiceXCustomFieldsFormat | Unset = UNSET,
) -> DetailedErrorResponse | ErrorResponse | Service | None:
    """Create Service

     Create a new Service. (See: [Create
    Service](https://developer.katanamrp.com/reference/createservice))

    Args:
        x_custom_fields_format (CreateServiceXCustomFieldsFormat | Unset):
        body (CreateServiceRequest): Request payload for creating a new service with variants and
            specifications Example: {'name': 'Assembly Service', 'uom': 'hours', 'category_name':
            'Manufacturing Services', 'additional_info': 'Professional product assembly service',
            'is_sellable': True, 'custom_field_collection_id': 1, 'variants': [{'sku': 'ASSM-001',
            'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | Service
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_custom_fields_format=x_custom_fields_format,
        )
    ).parsed
