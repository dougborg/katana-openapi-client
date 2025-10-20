from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.stocktake_row import StocktakeRow
from ...models.update_stocktake_row_request import UpdateStocktakeRowRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateStocktakeRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/stocktake_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | StocktakeRow | None:
    if response.status_code == 200:
        response_200 = StocktakeRow.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | StocktakeRow]:
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
    body: UpdateStocktakeRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | StocktakeRow]:
    """Update a stocktake row

     Updates the specified stocktake row by setting the values of the parameters passed. Any parameters
    not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStocktakeRowRequest): Request payload for updating an existing stocktake row
            Example: {'actual_quantity': 148.0, 'variance_quantity': -2.0, 'notes': 'Recount confirmed
            minor variance'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, StocktakeRow]]
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
    body: UpdateStocktakeRowRequest,
) -> DetailedErrorResponse | ErrorResponse | StocktakeRow | None:
    """Update a stocktake row

     Updates the specified stocktake row by setting the values of the parameters passed. Any parameters
    not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStocktakeRowRequest): Request payload for updating an existing stocktake row
            Example: {'actual_quantity': 148.0, 'variance_quantity': -2.0, 'notes': 'Recount confirmed
            minor variance'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, StocktakeRow]
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
    body: UpdateStocktakeRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | StocktakeRow]:
    """Update a stocktake row

     Updates the specified stocktake row by setting the values of the parameters passed. Any parameters
    not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStocktakeRowRequest): Request payload for updating an existing stocktake row
            Example: {'actual_quantity': 148.0, 'variance_quantity': -2.0, 'notes': 'Recount confirmed
            minor variance'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, StocktakeRow]]
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
    body: UpdateStocktakeRowRequest,
) -> DetailedErrorResponse | ErrorResponse | StocktakeRow | None:
    """Update a stocktake row

     Updates the specified stocktake row by setting the values of the parameters passed. Any parameters
    not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateStocktakeRowRequest): Request payload for updating an existing stocktake row
            Example: {'actual_quantity': 148.0, 'variance_quantity': -2.0, 'notes': 'Recount confirmed
            minor variance'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, StocktakeRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
