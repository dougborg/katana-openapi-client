from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.bin_transfer_row_list_response import BinTransferRowListResponse
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    source_bin_location_id: int | Unset = UNSET,
    target_bin_location_id: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["include_deleted"] = include_deleted

    params["bin_transfer_id"] = bin_transfer_id

    params["variant_id"] = variant_id

    params["source_bin_location_id"] = source_bin_location_id

    params["target_bin_location_id"] = target_bin_location_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bin_transfer_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BinTransferRowListResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = BinTransferRowListResponse.from_dict(response.json())

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
) -> Response[BinTransferRowListResponse | ErrorResponse]:
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
    bin_transfer_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    source_bin_location_id: int | Unset = UNSET,
    target_bin_location_id: int | Unset = UNSET,
) -> Response[BinTransferRowListResponse | ErrorResponse]:
    """List all bin transfer rows

     Returns a list of bin transfer rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_id (int | Unset):
        variant_id (int | Unset):
        source_bin_location_id (int | Unset):
        target_bin_location_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransferRowListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_id=bin_transfer_id,
        variant_id=variant_id,
        source_bin_location_id=source_bin_location_id,
        target_bin_location_id=target_bin_location_id,
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
    bin_transfer_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    source_bin_location_id: int | Unset = UNSET,
    target_bin_location_id: int | Unset = UNSET,
) -> BinTransferRowListResponse | ErrorResponse | None:
    """List all bin transfer rows

     Returns a list of bin transfer rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_id (int | Unset):
        variant_id (int | Unset):
        source_bin_location_id (int | Unset):
        target_bin_location_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransferRowListResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_id=bin_transfer_id,
        variant_id=variant_id,
        source_bin_location_id=source_bin_location_id,
        target_bin_location_id=target_bin_location_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    bin_transfer_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    source_bin_location_id: int | Unset = UNSET,
    target_bin_location_id: int | Unset = UNSET,
) -> Response[BinTransferRowListResponse | ErrorResponse]:
    """List all bin transfer rows

     Returns a list of bin transfer rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_id (int | Unset):
        variant_id (int | Unset):
        source_bin_location_id (int | Unset):
        target_bin_location_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinTransferRowListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        bin_transfer_id=bin_transfer_id,
        variant_id=variant_id,
        source_bin_location_id=source_bin_location_id,
        target_bin_location_id=target_bin_location_id,
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
    bin_transfer_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    source_bin_location_id: int | Unset = UNSET,
    target_bin_location_id: int | Unset = UNSET,
) -> BinTransferRowListResponse | ErrorResponse | None:
    """List all bin transfer rows

     Returns a list of bin transfer rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        bin_transfer_id (int | Unset):
        variant_id (int | Unset):
        source_bin_location_id (int | Unset):
        target_bin_location_id (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinTransferRowListResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            include_deleted=include_deleted,
            bin_transfer_id=bin_transfer_id,
            variant_id=variant_id,
            source_bin_location_id=source_bin_location_id,
            target_bin_location_id=target_bin_location_id,
        )
    ).parsed
