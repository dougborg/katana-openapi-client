from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_price_list_request import CreatePriceListRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.price_list import PriceList


def _get_kwargs(
    *,
    body: CreatePriceListRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/price_lists",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | PriceList | None:
    if response.status_code == 200:
        response_200 = PriceList.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[DetailedErrorResponse | ErrorResponse | PriceList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | PriceList]:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest): Request payload for creating a new price list with market-
            specific pricing configurations and time-based validity Example: {'name': 'Premium
            Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage': 25.0,
            'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, PriceList]]
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
    body: CreatePriceListRequest,
) -> DetailedErrorResponse | ErrorResponse | PriceList | None:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest): Request payload for creating a new price list with market-
            specific pricing configurations and time-based validity Example: {'name': 'Premium
            Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage': 25.0,
            'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, PriceList]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | PriceList]:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest): Request payload for creating a new price list with market-
            specific pricing configurations and time-based validity Example: {'name': 'Premium
            Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage': 25.0,
            'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, PriceList]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRequest,
) -> DetailedErrorResponse | ErrorResponse | PriceList | None:
    """Create a price list

     Creates a new price list.

    Args:
        body (CreatePriceListRequest): Request payload for creating a new price list with market-
            specific pricing configurations and time-based validity Example: {'name': 'Premium
            Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage': 25.0,
            'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, PriceList]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
