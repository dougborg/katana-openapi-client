from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_serial_numbers_request import CreateSerialNumbersRequest
from ...models.create_serial_numbers_response import CreateSerialNumbersResponse
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    body: CreateSerialNumbersRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/serial_numbers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = CreateSerialNumbersResponse.from_dict(response.json())

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
) -> Response[CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSerialNumbersRequest,
) -> Response[CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]:
    """Create serial numbers

     Mints new or transfers existing serial numbers to a resource.

    **Write semantics differ by ``resource_type``** (see
    ``CreateSerialNumberResourceType``):

    - **Mint** (``ManufacturingOrder``, ``PurchaseOrderRow``) — the
      serial-number string doesn't need to pre-exist. The API creates a
      new record and links it to the target resource.
    - **Transfer** (``SalesOrderRow``, ``StockTransferRow``,
      ``StockAdjustmentRow``) — the serial-number string MUST already
      exist (typically attached to a ManufacturingOrder output). The
      API moves the linkage from its current resource to the target.
      If the string isn't anywhere yet, the entry lands in ``failed``
      with ``reason: MISSING`` — the call still returns 200.

    **Partial failure is the norm, not the exception.** The response
    carries ``successful`` AND ``failed`` arrays; consumers must
    handle both. A 200 status does NOT mean every input was applied —
    check ``failed`` to learn which strings the API rejected.

    **422 cases:** non-existent ``resource_id`` returns
    ``422 UnprocessableEntityError`` with detail ``No entity found``
    (not 404). Invalid ``resource_type`` (e.g. ``Production``)
    returns 422 with an Ajv-style validation detail.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Request payload for creating serial numbers for a
            resource

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]
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
    body: CreateSerialNumbersRequest,
) -> CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    """Create serial numbers

     Mints new or transfers existing serial numbers to a resource.

    **Write semantics differ by ``resource_type``** (see
    ``CreateSerialNumberResourceType``):

    - **Mint** (``ManufacturingOrder``, ``PurchaseOrderRow``) — the
      serial-number string doesn't need to pre-exist. The API creates a
      new record and links it to the target resource.
    - **Transfer** (``SalesOrderRow``, ``StockTransferRow``,
      ``StockAdjustmentRow``) — the serial-number string MUST already
      exist (typically attached to a ManufacturingOrder output). The
      API moves the linkage from its current resource to the target.
      If the string isn't anywhere yet, the entry lands in ``failed``
      with ``reason: MISSING`` — the call still returns 200.

    **Partial failure is the norm, not the exception.** The response
    carries ``successful`` AND ``failed`` arrays; consumers must
    handle both. A 200 status does NOT mean every input was applied —
    check ``failed`` to learn which strings the API rejected.

    **422 cases:** non-existent ``resource_id`` returns
    ``422 UnprocessableEntityError`` with detail ``No entity found``
    (not 404). Invalid ``resource_type`` (e.g. ``Production``)
    returns 422 with an Ajv-style validation detail.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Request payload for creating serial numbers for a
            resource

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSerialNumbersRequest,
) -> Response[CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]:
    """Create serial numbers

     Mints new or transfers existing serial numbers to a resource.

    **Write semantics differ by ``resource_type``** (see
    ``CreateSerialNumberResourceType``):

    - **Mint** (``ManufacturingOrder``, ``PurchaseOrderRow``) — the
      serial-number string doesn't need to pre-exist. The API creates a
      new record and links it to the target resource.
    - **Transfer** (``SalesOrderRow``, ``StockTransferRow``,
      ``StockAdjustmentRow``) — the serial-number string MUST already
      exist (typically attached to a ManufacturingOrder output). The
      API moves the linkage from its current resource to the target.
      If the string isn't anywhere yet, the entry lands in ``failed``
      with ``reason: MISSING`` — the call still returns 200.

    **Partial failure is the norm, not the exception.** The response
    carries ``successful`` AND ``failed`` arrays; consumers must
    handle both. A 200 status does NOT mean every input was applied —
    check ``failed`` to learn which strings the API rejected.

    **422 cases:** non-existent ``resource_id`` returns
    ``422 UnprocessableEntityError`` with detail ``No entity found``
    (not 404). Invalid ``resource_type`` (e.g. ``Production``)
    returns 422 with an Ajv-style validation detail.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Request payload for creating serial numbers for a
            resource

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSerialNumbersRequest,
) -> CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    """Create serial numbers

     Mints new or transfers existing serial numbers to a resource.

    **Write semantics differ by ``resource_type``** (see
    ``CreateSerialNumberResourceType``):

    - **Mint** (``ManufacturingOrder``, ``PurchaseOrderRow``) — the
      serial-number string doesn't need to pre-exist. The API creates a
      new record and links it to the target resource.
    - **Transfer** (``SalesOrderRow``, ``StockTransferRow``,
      ``StockAdjustmentRow``) — the serial-number string MUST already
      exist (typically attached to a ManufacturingOrder output). The
      API moves the linkage from its current resource to the target.
      If the string isn't anywhere yet, the entry lands in ``failed``
      with ``reason: MISSING`` — the call still returns 200.

    **Partial failure is the norm, not the exception.** The response
    carries ``successful`` AND ``failed`` arrays; consumers must
    handle both. A 200 status does NOT mean every input was applied —
    check ``failed`` to learn which strings the API rejected.

    **422 cases:** non-existent ``resource_id`` returns
    ``422 UnprocessableEntityError`` with detail ``No entity found``
    (not 404). Invalid ``resource_type`` (e.g. ``Production``)
    returns 422 with an Ajv-style validation detail.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Request payload for creating serial numbers for a
            resource

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
