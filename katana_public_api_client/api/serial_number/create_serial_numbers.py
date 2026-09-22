from http import HTTPStatus
from typing import Any, cast

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
) -> Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = CreateSerialNumbersResponse.from_dict(response.json())

        return response_200

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[
    Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
]:
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
) -> Response[
    Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
]:
    """Attach serial numbers

     Attaches pre-existing serial-number strings to a resource. This endpoint
    did not mint a new string for any tested resource type or manufacturing-
    order state. Serial identities are created by inventory-producing
    workflows such as production and goods receipt.

    **Error cases** (verified live 2026-07-14, #980): a non-existent
    ``resource_id`` returns ``404 NotFoundError`` with a type-specific
    message (e.g. ``manufacturing order <id> not found`` /
    ``production <id> not found``). A ``resource_type`` outside the
    ``CreateSerialNumberResourceType`` enum returns ``422`` with an
    Ajv-style validation detail. Unknown, duplicate, and mixed
    valid/invalid strings hard-fail the whole request with ``422``; the
    legacy ``failed`` array was never observed. A completed manufacturing
    order can instead reject because it has no remaining quantity and
    direct callers to update completed production traceability.

    Manual attachment to valid standalone and make-to-order manufacturing
    orders returned ``404`` in September 2026, before and after production.
    Production and fulfillment can use their unified ``traceability``
    contracts without a successful call to this endpoint.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Attach existing serial-number strings to a resource.
            Only resource_id is required by the gateway. Omitting resource_type is accepted as a no-op
            (204 No Content); supply resource_type and serial_numbers to attempt an attachment (#830,
            #983). Unknown strings abort with 422; this endpoint did not mint new strings in current
            live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]
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
) -> Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    """Attach serial numbers

     Attaches pre-existing serial-number strings to a resource. This endpoint
    did not mint a new string for any tested resource type or manufacturing-
    order state. Serial identities are created by inventory-producing
    workflows such as production and goods receipt.

    **Error cases** (verified live 2026-07-14, #980): a non-existent
    ``resource_id`` returns ``404 NotFoundError`` with a type-specific
    message (e.g. ``manufacturing order <id> not found`` /
    ``production <id> not found``). A ``resource_type`` outside the
    ``CreateSerialNumberResourceType`` enum returns ``422`` with an
    Ajv-style validation detail. Unknown, duplicate, and mixed
    valid/invalid strings hard-fail the whole request with ``422``; the
    legacy ``failed`` array was never observed. A completed manufacturing
    order can instead reject because it has no remaining quantity and
    direct callers to update completed production traceability.

    Manual attachment to valid standalone and make-to-order manufacturing
    orders returned ``404`` in September 2026, before and after production.
    Production and fulfillment can use their unified ``traceability``
    contracts without a successful call to this endpoint.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Attach existing serial-number strings to a resource.
            Only resource_id is required by the gateway. Omitting resource_type is accepted as a no-op
            (204 No Content); supply resource_type and serial_numbers to attempt an attachment (#830,
            #983). Unknown strings abort with 422; this endpoint did not mint new strings in current
            live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSerialNumbersRequest,
) -> Response[
    Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
]:
    """Attach serial numbers

     Attaches pre-existing serial-number strings to a resource. This endpoint
    did not mint a new string for any tested resource type or manufacturing-
    order state. Serial identities are created by inventory-producing
    workflows such as production and goods receipt.

    **Error cases** (verified live 2026-07-14, #980): a non-existent
    ``resource_id`` returns ``404 NotFoundError`` with a type-specific
    message (e.g. ``manufacturing order <id> not found`` /
    ``production <id> not found``). A ``resource_type`` outside the
    ``CreateSerialNumberResourceType`` enum returns ``422`` with an
    Ajv-style validation detail. Unknown, duplicate, and mixed
    valid/invalid strings hard-fail the whole request with ``422``; the
    legacy ``failed`` array was never observed. A completed manufacturing
    order can instead reject because it has no remaining quantity and
    direct callers to update completed production traceability.

    Manual attachment to valid standalone and make-to-order manufacturing
    orders returned ``404`` in September 2026, before and after production.
    Production and fulfillment can use their unified ``traceability``
    contracts without a successful call to this endpoint.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Attach existing serial-number strings to a resource.
            Only resource_id is required by the gateway. Omitting resource_type is accepted as a no-op
            (204 No Content); supply resource_type and serial_numbers to attempt an attachment (#830,
            #983). Unknown strings abort with 422; this endpoint did not mint new strings in current
            live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse]
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
) -> Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse | None:
    """Attach serial numbers

     Attaches pre-existing serial-number strings to a resource. This endpoint
    did not mint a new string for any tested resource type or manufacturing-
    order state. Serial identities are created by inventory-producing
    workflows such as production and goods receipt.

    **Error cases** (verified live 2026-07-14, #980): a non-existent
    ``resource_id`` returns ``404 NotFoundError`` with a type-specific
    message (e.g. ``manufacturing order <id> not found`` /
    ``production <id> not found``). A ``resource_type`` outside the
    ``CreateSerialNumberResourceType`` enum returns ``422`` with an
    Ajv-style validation detail. Unknown, duplicate, and mixed
    valid/invalid strings hard-fail the whole request with ``422``; the
    legacy ``failed`` array was never observed. A completed manufacturing
    order can instead reject because it has no remaining quantity and
    direct callers to update completed production traceability.

    Manual attachment to valid standalone and make-to-order manufacturing
    orders returned ``404`` in September 2026, before and after production.
    Production and fulfillment can use their unified ``traceability``
    contracts without a successful call to this endpoint.

    **Transfer response quirks:** on a successful transfer the moved
    record's ``transaction_id`` may be the literal string
    ``undefined`` and ``resource_id`` may be ``null`` — re-fetch via
    ``GET /serial_numbers`` to confirm the landing state.

    Args:
        body (CreateSerialNumbersRequest): Attach existing serial-number strings to a resource.
            Only resource_id is required by the gateway. Omitting resource_type is accepted as a no-op
            (204 No Content); supply resource_type and serial_numbers to attempt an attachment (#830,
            #983). Unknown strings abort with 422; this endpoint did not mint new strings in current
            live probes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | CreateSerialNumbersResponse | DetailedErrorResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
