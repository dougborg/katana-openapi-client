from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.bin_inventory_granularity import BinInventoryGranularity
from ...models.bin_inventory_list_response import BinInventoryListResponse
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    granularity: BinInventoryGranularity | Unset = UNSET,
    location_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    bin_location_id: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    serial_number_id: str | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_granularity: str | Unset = UNSET
    if not isinstance(granularity, Unset):
        json_granularity = granularity.value

    params["granularity"] = json_granularity

    params["location_id"] = location_id

    params["variant_id"] = variant_id

    params["bin_location_id"] = bin_location_id

    params["batch_id"] = batch_id

    params["serial_number_id"] = serial_number_id

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bin_inventory",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BinInventoryListResponse | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = BinInventoryListResponse.from_dict(response.json())

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
) -> Response[BinInventoryListResponse | DetailedErrorResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    granularity: BinInventoryGranularity | Unset = UNSET,
    location_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    bin_location_id: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    serial_number_id: str | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> Response[BinInventoryListResponse | DetailedErrorResponse | ErrorResponse]:
    """List bin inventory levels

     Returns per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns
    one row per (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the
    matching traceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,
    `quantity_committed`, and `quantity_expected`.

    A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that
    axis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to
    target those rows. Bin inventory levels are computed asynchronously and are eventually consistent.

    Args:
        granularity (BinInventoryGranularity | Unset): Row granularity for a bin inventory query.
            `VARIANT` returns one row per
            (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further
            by the matching traceability axis.
        location_id (int | Unset):
        variant_id (int | Unset):
        bin_location_id (str | Unset):
        batch_id (str | Unset):
        serial_number_id (str | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinInventoryListResponse | DetailedErrorResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        granularity=granularity,
        location_id=location_id,
        variant_id=variant_id,
        bin_location_id=bin_location_id,
        batch_id=batch_id,
        serial_number_id=serial_number_id,
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    granularity: BinInventoryGranularity | Unset = UNSET,
    location_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    bin_location_id: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    serial_number_id: str | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> BinInventoryListResponse | DetailedErrorResponse | ErrorResponse | None:
    """List bin inventory levels

     Returns per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns
    one row per (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the
    matching traceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,
    `quantity_committed`, and `quantity_expected`.

    A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that
    axis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to
    target those rows. Bin inventory levels are computed asynchronously and are eventually consistent.

    Args:
        granularity (BinInventoryGranularity | Unset): Row granularity for a bin inventory query.
            `VARIANT` returns one row per
            (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further
            by the matching traceability axis.
        location_id (int | Unset):
        variant_id (int | Unset):
        bin_location_id (str | Unset):
        batch_id (str | Unset):
        serial_number_id (str | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinInventoryListResponse | DetailedErrorResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        granularity=granularity,
        location_id=location_id,
        variant_id=variant_id,
        bin_location_id=bin_location_id,
        batch_id=batch_id,
        serial_number_id=serial_number_id,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    granularity: BinInventoryGranularity | Unset = UNSET,
    location_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    bin_location_id: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    serial_number_id: str | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> Response[BinInventoryListResponse | DetailedErrorResponse | ErrorResponse]:
    """List bin inventory levels

     Returns per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns
    one row per (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the
    matching traceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,
    `quantity_committed`, and `quantity_expected`.

    A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that
    axis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to
    target those rows. Bin inventory levels are computed asynchronously and are eventually consistent.

    Args:
        granularity (BinInventoryGranularity | Unset): Row granularity for a bin inventory query.
            `VARIANT` returns one row per
            (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further
            by the matching traceability axis.
        location_id (int | Unset):
        variant_id (int | Unset):
        bin_location_id (str | Unset):
        batch_id (str | Unset):
        serial_number_id (str | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[BinInventoryListResponse | DetailedErrorResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        granularity=granularity,
        location_id=location_id,
        variant_id=variant_id,
        bin_location_id=bin_location_id,
        batch_id=batch_id,
        serial_number_id=serial_number_id,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    granularity: BinInventoryGranularity | Unset = UNSET,
    location_id: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    bin_location_id: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    serial_number_id: str | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
) -> BinInventoryListResponse | DetailedErrorResponse | ErrorResponse | None:
    """List bin inventory levels

     Returns per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns
    one row per (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the
    matching traceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,
    `quantity_committed`, and `quantity_expected`.

    A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that
    axis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to
    target those rows. Bin inventory levels are computed asynchronously and are eventually consistent.

    Args:
        granularity (BinInventoryGranularity | Unset): Row granularity for a bin inventory query.
            `VARIANT` returns one row per
            (location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further
            by the matching traceability axis.
        location_id (int | Unset):
        variant_id (int | Unset):
        bin_location_id (str | Unset):
        batch_id (str | Unset):
        serial_number_id (str | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        BinInventoryListResponse | DetailedErrorResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            granularity=granularity,
            location_id=location_id,
            variant_id=variant_id,
            bin_location_id=bin_location_id,
            batch_id=batch_id,
            serial_number_id=serial_number_id,
            limit=limit,
            page=page,
        )
    ).parsed
