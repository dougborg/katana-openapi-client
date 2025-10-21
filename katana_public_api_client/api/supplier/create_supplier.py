from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_supplier_request import CreateSupplierRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.supplier import Supplier


def _get_kwargs(
    *,
    body: CreateSupplierRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/suppliers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | Supplier | None:
    if response.status_code == 200:
        response_200 = Supplier.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | Supplier]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Supplier]:
    """Create a supplier

     Creates a new supplier object.

    Args:
        body (CreateSupplierRequest): Request payload for creating a new supplier with contact
            information and addresses Example: {'name': 'Premium Kitchen Supplies Ltd', 'currency':
            'USD', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'comment': 'Primary
            supplier for kitchen equipment and utensils', 'addresses': [{'line_1': '1250 Industrial
            Blvd', 'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country':
            'US'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Supplier]]
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
    body: CreateSupplierRequest,
) -> DetailedErrorResponse | ErrorResponse | Supplier | None:
    """Create a supplier

     Creates a new supplier object.

    Args:
        body (CreateSupplierRequest): Request payload for creating a new supplier with contact
            information and addresses Example: {'name': 'Premium Kitchen Supplies Ltd', 'currency':
            'USD', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'comment': 'Primary
            supplier for kitchen equipment and utensils', 'addresses': [{'line_1': '1250 Industrial
            Blvd', 'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country':
            'US'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Supplier]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Supplier]:
    """Create a supplier

     Creates a new supplier object.

    Args:
        body (CreateSupplierRequest): Request payload for creating a new supplier with contact
            information and addresses Example: {'name': 'Premium Kitchen Supplies Ltd', 'currency':
            'USD', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'comment': 'Primary
            supplier for kitchen equipment and utensils', 'addresses': [{'line_1': '1250 Industrial
            Blvd', 'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country':
            'US'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Supplier]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierRequest,
) -> DetailedErrorResponse | ErrorResponse | Supplier | None:
    """Create a supplier

     Creates a new supplier object.

    Args:
        body (CreateSupplierRequest): Request payload for creating a new supplier with contact
            information and addresses Example: {'name': 'Premium Kitchen Supplies Ltd', 'currency':
            'USD', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'comment': 'Primary
            supplier for kitchen equipment and utensils', 'addresses': [{'line_1': '1250 Industrial
            Blvd', 'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country':
            'US'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Supplier]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
