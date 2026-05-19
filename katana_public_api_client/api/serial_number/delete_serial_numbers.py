from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.delete_serial_numbers_request import DeleteSerialNumbersRequest
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    body: DeleteSerialNumbersRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/serial_numbers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ErrorResponse | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteSerialNumbersRequest,
) -> Response[Any | ErrorResponse]:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    **DELETE is unconditionally idempotent.** Empirically (live-API
    probes 2026-05-19) the endpoint returns 204 No Content for every
    request variant tested: valid id, already-deleted id, mixed
    valid+invalid id batches, pure-invalid id, and ``resource_id``
    mismatch between body and the SN's actual parent. The endpoint
    does NOT validate the request body — callers cannot detect
    ``id didn't exist`` or ``id belongs to wrong resource`` via
    the response. If strong confirmation is needed, follow up with a
    ``GET /serial_numbers`` filtered by ``resource_id`` and verify
    the deleted ids are absent.

    Args:
        body (DeleteSerialNumbersRequest): Request payload for deleting serial numbers from a
            resource. The
            delete is scoped to a single resource (``resource_type`` +
            ``resource_id``) and a list of serial-number IDs.
             Example: {'resource_type': 'ManufacturingOrder', 'resource_id': 3001, 'ids': [1001,
            1002]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | ErrorResponse]
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
    body: DeleteSerialNumbersRequest,
) -> Any | ErrorResponse | None:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    **DELETE is unconditionally idempotent.** Empirically (live-API
    probes 2026-05-19) the endpoint returns 204 No Content for every
    request variant tested: valid id, already-deleted id, mixed
    valid+invalid id batches, pure-invalid id, and ``resource_id``
    mismatch between body and the SN's actual parent. The endpoint
    does NOT validate the request body — callers cannot detect
    ``id didn't exist`` or ``id belongs to wrong resource`` via
    the response. If strong confirmation is needed, follow up with a
    ``GET /serial_numbers`` filtered by ``resource_id`` and verify
    the deleted ids are absent.

    Args:
        body (DeleteSerialNumbersRequest): Request payload for deleting serial numbers from a
            resource. The
            delete is scoped to a single resource (``resource_type`` +
            ``resource_id``) and a list of serial-number IDs.
             Example: {'resource_type': 'ManufacturingOrder', 'resource_id': 3001, 'ids': [1001,
            1002]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | ErrorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteSerialNumbersRequest,
) -> Response[Any | ErrorResponse]:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    **DELETE is unconditionally idempotent.** Empirically (live-API
    probes 2026-05-19) the endpoint returns 204 No Content for every
    request variant tested: valid id, already-deleted id, mixed
    valid+invalid id batches, pure-invalid id, and ``resource_id``
    mismatch between body and the SN's actual parent. The endpoint
    does NOT validate the request body — callers cannot detect
    ``id didn't exist`` or ``id belongs to wrong resource`` via
    the response. If strong confirmation is needed, follow up with a
    ``GET /serial_numbers`` filtered by ``resource_id`` and verify
    the deleted ids are absent.

    Args:
        body (DeleteSerialNumbersRequest): Request payload for deleting serial numbers from a
            resource. The
            delete is scoped to a single resource (``resource_type`` +
            ``resource_id``) and a list of serial-number IDs.
             Example: {'resource_type': 'ManufacturingOrder', 'resource_id': 3001, 'ids': [1001,
            1002]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Any | ErrorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteSerialNumbersRequest,
) -> Any | ErrorResponse | None:
    """Delete serial numbers

     Deletes serial numbers for a resource.

    **DELETE is unconditionally idempotent.** Empirically (live-API
    probes 2026-05-19) the endpoint returns 204 No Content for every
    request variant tested: valid id, already-deleted id, mixed
    valid+invalid id batches, pure-invalid id, and ``resource_id``
    mismatch between body and the SN's actual parent. The endpoint
    does NOT validate the request body — callers cannot detect
    ``id didn't exist`` or ``id belongs to wrong resource`` via
    the response. If strong confirmation is needed, follow up with a
    ``GET /serial_numbers`` filtered by ``resource_id`` and verify
    the deleted ids are absent.

    Args:
        body (DeleteSerialNumbersRequest): Request payload for deleting serial numbers from a
            resource. The
            delete is scoped to a single resource (``resource_type`` +
            ``resource_id``) and a list of serial-number IDs.
             Example: {'resource_type': 'ManufacturingOrder', 'resource_id': 3001, 'ids': [1001,
            1002]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Any | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
