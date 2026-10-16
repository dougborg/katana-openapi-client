from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.unassigned_batch_transaction import UnassignedBatchTransaction
from ...models.unassigned_batch_transaction_list_response import (
    UnassignedBatchTransactionListResponse,
)


def _get_kwargs(
    id: int,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_return_rows/{id}/unassigned_batch_transactions".format(
            id=quote(str(id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
    | None
):
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> list[UnassignedBatchTransaction] | UnassignedBatchTransactionListResponse:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                response_200_type_0 = []
                _response_200_type_0 = data
                for response_200_type_0_item_data in _response_200_type_0:
                    response_200_type_0_item = UnassignedBatchTransaction.from_dict(
                        cast(Mapping[str, Any], response_200_type_0_item_data)
                    )

                    response_200_type_0.append(response_200_type_0_item)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = UnassignedBatchTransactionListResponse.from_dict(
                cast(Mapping[str, Any], data)
            )

            return response_200_type_1

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
) -> Response[
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
]:
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
) -> Response[
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
]:
    """Get unassigned batch transactions for a sales return row

     Retrieves unassigned batch transactions associated with a sales return row.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | list[UnassignedBatchTransaction] | UnassignedBatchTransactionListResponse]
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
) -> (
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
    | None
):
    """Get unassigned batch transactions for a sales return row

     Retrieves unassigned batch transactions associated with a sales return row.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | list[UnassignedBatchTransaction] | UnassignedBatchTransactionListResponse
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
]:
    """Get unassigned batch transactions for a sales return row

     Retrieves unassigned batch transactions associated with a sales return row.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | list[UnassignedBatchTransaction] | UnassignedBatchTransactionListResponse]
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
) -> (
    ErrorResponse
    | list[UnassignedBatchTransaction]
    | UnassignedBatchTransactionListResponse
    | None
):
    """Get unassigned batch transactions for a sales return row

     Retrieves unassigned batch transactions associated with a sales return row.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | list[UnassignedBatchTransaction] | UnassignedBatchTransactionListResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
