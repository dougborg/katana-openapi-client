from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.bin_transfer import BinTransfer
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.update_bin_transfer_request import UpdateBinTransferRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateBinTransferRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/bin_transfers/{id}".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BinTransfer | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = BinTransfer.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[BinTransfer | DetailedErrorResponse | ErrorResponse]:
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
    body: UpdateBinTransferRequest,
) -> Response[BinTransfer | DetailedErrorResponse | ErrorResponse]:
    """Update a bin transfer

     Updates a bin transfer's header fields.

    Args:
        id (int):
        body (UpdateBinTransferRequest): Request payload for updating a bin transfer's header
            fields. Example: {'bin_transfer_number': 'BT-1', 'additional_info': 'updated note'}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransfer | DetailedErrorResponse | ErrorResponse]
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
    body: UpdateBinTransferRequest,
) -> BinTransfer | DetailedErrorResponse | ErrorResponse | None:
    """Update a bin transfer

     Updates a bin transfer's header fields.

    Args:
        id (int):
        body (UpdateBinTransferRequest): Request payload for updating a bin transfer's header
            fields. Example: {'bin_transfer_number': 'BT-1', 'additional_info': 'updated note'}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransfer | DetailedErrorResponse | ErrorResponse
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
    body: UpdateBinTransferRequest,
) -> Response[BinTransfer | DetailedErrorResponse | ErrorResponse]:
    """Update a bin transfer

     Updates a bin transfer's header fields.

    Args:
        id (int):
        body (UpdateBinTransferRequest): Request payload for updating a bin transfer's header
            fields. Example: {'bin_transfer_number': 'BT-1', 'additional_info': 'updated note'}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransfer | DetailedErrorResponse | ErrorResponse]
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
    body: UpdateBinTransferRequest,
) -> BinTransfer | DetailedErrorResponse | ErrorResponse | None:
    """Update a bin transfer

     Updates a bin transfer's header fields.

    Args:
        id (int):
        body (UpdateBinTransferRequest): Request payload for updating a bin transfer's header
            fields. Example: {'bin_transfer_number': 'BT-1', 'additional_info': 'updated note'}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransfer | DetailedErrorResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
