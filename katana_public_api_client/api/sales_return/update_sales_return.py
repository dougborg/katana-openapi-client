from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_return import SalesReturn
from ...models.update_sales_return_request import UpdateSalesReturnRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateSalesReturnRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/sales_returns/{id}".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    if response.status_code == 200:
        response_200 = SalesReturn.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
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
    body: UpdateSalesReturnRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
    """Update a sales return

     Updates the specified sales return by setting the values of the parameters passed. Any parameters
    not provided
    will be left unchanged.

    Args:
        id (int):
        body (UpdateSalesReturnRequest): Request payload for updating an existing sales return
            Example: {'status': 'RETURNED_ALL', 'return_date': '2023-10-12T10:00:00Z', 'order_no':
            'SR-2023-001', 'return_location_id': 1, 'additional_info': 'Customer reported damaged
            items during shipping'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesReturn]
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
    body: UpdateSalesReturnRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    """Update a sales return

     Updates the specified sales return by setting the values of the parameters passed. Any parameters
    not provided
    will be left unchanged.

    Args:
        id (int):
        body (UpdateSalesReturnRequest): Request payload for updating an existing sales return
            Example: {'status': 'RETURNED_ALL', 'return_date': '2023-10-12T10:00:00Z', 'order_no':
            'SR-2023-001', 'return_location_id': 1, 'additional_info': 'Customer reported damaged
            items during shipping'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesReturn
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
    body: UpdateSalesReturnRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
    """Update a sales return

     Updates the specified sales return by setting the values of the parameters passed. Any parameters
    not provided
    will be left unchanged.

    Args:
        id (int):
        body (UpdateSalesReturnRequest): Request payload for updating an existing sales return
            Example: {'status': 'RETURNED_ALL', 'return_date': '2023-10-12T10:00:00Z', 'order_no':
            'SR-2023-001', 'return_location_id': 1, 'additional_info': 'Customer reported damaged
            items during shipping'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | SalesReturn]
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
    body: UpdateSalesReturnRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    """Update a sales return

     Updates the specified sales return by setting the values of the parameters passed. Any parameters
    not provided
    will be left unchanged.

    Args:
        id (int):
        body (UpdateSalesReturnRequest): Request payload for updating an existing sales return
            Example: {'status': 'RETURNED_ALL', 'return_date': '2023-10-12T10:00:00Z', 'order_no':
            'SR-2023-001', 'return_location_id': 1, 'additional_info': 'Customer reported damaged
            items during shipping'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | SalesReturn
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
