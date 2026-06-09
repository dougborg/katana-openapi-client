from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.bin_transfer_list_response import BinTransferListResponse
from ...models.bin_transfer_status import BinTransferStatus
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_number: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: BinTransferStatus | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["include_deleted"] = include_deleted

    params["bin_transfer_number"] = bin_transfer_number

    params["location_id"] = location_id

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bin_transfers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BinTransferListResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = BinTransferListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

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
) -> Response[BinTransferListResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_number: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: BinTransferStatus | Unset = UNSET,
) -> Response[BinTransferListResponse | ErrorResponse]:
    """List all bin transfers

     Returns a list of bin transfers.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_number (str | Unset):
        location_id (int | Unset):
        status (BinTransferStatus | Unset): Lifecycle status of a bin transfer. New transfers
            start in `CREATED`; status
            changes are applied through the dedicated status endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransferListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_number=bin_transfer_number,
        location_id=location_id,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_number: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: BinTransferStatus | Unset = UNSET,
) -> BinTransferListResponse | ErrorResponse | None:
    """List all bin transfers

     Returns a list of bin transfers.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_number (str | Unset):
        location_id (int | Unset):
        status (BinTransferStatus | Unset): Lifecycle status of a bin transfer. New transfers
            start in `CREATED`; status
            changes are applied through the dedicated status endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransferListResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_number=bin_transfer_number,
        location_id=location_id,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_number: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: BinTransferStatus | Unset = UNSET,
) -> Response[BinTransferListResponse | ErrorResponse]:
    """List all bin transfers

     Returns a list of bin transfers.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_number (str | Unset):
        location_id (int | Unset):
        status (BinTransferStatus | Unset): Lifecycle status of a bin transfer. New transfers
            start in `CREATED`; status
            changes are applied through the dedicated status endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransferListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_number=bin_transfer_number,
        location_id=location_id,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_number: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: BinTransferStatus | Unset = UNSET,
) -> BinTransferListResponse | ErrorResponse | None:
    """List all bin transfers

     Returns a list of bin transfers.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_number (str | Unset):
        location_id (int | Unset):
        status (BinTransferStatus | Unset): Lifecycle status of a bin transfer. New transfers
            start in `CREATED`; status
            changes are applied through the dedicated status endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransferListResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            include_deleted=include_deleted,
            bin_transfer_number=bin_transfer_number,
            location_id=location_id,
            status=status,
        )
    ).parsed
