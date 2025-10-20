from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_price_list_row_request import CreatePriceListRowRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.price_list_row import PriceListRow


def _get_kwargs(
    *,
    body: CreatePriceListRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/price_list_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | list["PriceListRow"] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = PriceListRow.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[DetailedErrorResponse | ErrorResponse | list["PriceListRow"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | list["PriceListRow"]]:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest): Request payload for adding a product variant with
            specific pricing to a price list for customer-specific pricing management Example:
            {'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, list['PriceListRow']]]
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
    body: CreatePriceListRowRequest,
) -> DetailedErrorResponse | ErrorResponse | list["PriceListRow"] | None:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest): Request payload for adding a product variant with
            specific pricing to a price list for customer-specific pricing management Example:
            {'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, list['PriceListRow']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | list["PriceListRow"]]:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest): Request payload for adding a product variant with
            specific pricing to a price list for customer-specific pricing management Example:
            {'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, list['PriceListRow']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListRowRequest,
) -> DetailedErrorResponse | ErrorResponse | list["PriceListRow"] | None:
    """Create a price list row

     Creates a new price list row.

    Args:
        body (CreatePriceListRowRequest): Request payload for adding a product variant with
            specific pricing to a price list for customer-specific pricing management Example:
            {'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, list['PriceListRow']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
