import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_product_operation_rows_response_200 import (
    GetAllProductOperationRowsResponse200,
)


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    product_id: Unset | int = UNSET,
    operation_id: Unset | int = UNSET,
    product_variant_id: Unset | int = UNSET,
    operation_name: Unset | str = UNSET,
    resource_name: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    product_operation_row_id: Unset | int = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["product_id"] = product_id

    params["operation_id"] = operation_id

    params["product_variant_id"] = product_variant_id

    params["operation_name"] = operation_name

    params["resource_name"] = resource_name

    params["resource_id"] = resource_id

    params["product_operation_row_id"] = product_operation_row_id

    json_created_at_min: Unset | str = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: Unset | str = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: Unset | str = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: Unset | str = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/product_operation_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | GetAllProductOperationRowsResponse200 | None:
    if response.status_code == 200:
        response_200 = GetAllProductOperationRowsResponse200.from_dict(response.json())

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
) -> Response[ErrorResponse | GetAllProductOperationRowsResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    product_id: Unset | int = UNSET,
    operation_id: Unset | int = UNSET,
    product_variant_id: Unset | int = UNSET,
    operation_name: Unset | str = UNSET,
    resource_name: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    product_operation_row_id: Unset | int = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | GetAllProductOperationRowsResponse200]:
    """List product operation rows

     Returns a list of product operation rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        product_id (Union[Unset, int]):
        operation_id (Union[Unset, int]):
        product_variant_id (Union[Unset, int]):
        operation_name (Union[Unset, str]):
        resource_name (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        product_operation_row_id (Union[Unset, int]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, GetAllProductOperationRowsResponse200]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        product_id=product_id,
        operation_id=operation_id,
        product_variant_id=product_variant_id,
        operation_name=operation_name,
        resource_name=resource_name,
        resource_id=resource_id,
        product_operation_row_id=product_operation_row_id,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    product_id: Unset | int = UNSET,
    operation_id: Unset | int = UNSET,
    product_variant_id: Unset | int = UNSET,
    operation_name: Unset | str = UNSET,
    resource_name: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    product_operation_row_id: Unset | int = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | GetAllProductOperationRowsResponse200 | None:
    """List product operation rows

     Returns a list of product operation rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        product_id (Union[Unset, int]):
        operation_id (Union[Unset, int]):
        product_variant_id (Union[Unset, int]):
        operation_name (Union[Unset, str]):
        resource_name (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        product_operation_row_id (Union[Unset, int]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, GetAllProductOperationRowsResponse200]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        product_id=product_id,
        operation_id=operation_id,
        product_variant_id=product_variant_id,
        operation_name=operation_name,
        resource_name=resource_name,
        resource_id=resource_id,
        product_operation_row_id=product_operation_row_id,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    product_id: Unset | int = UNSET,
    operation_id: Unset | int = UNSET,
    product_variant_id: Unset | int = UNSET,
    operation_name: Unset | str = UNSET,
    resource_name: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    product_operation_row_id: Unset | int = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | GetAllProductOperationRowsResponse200]:
    """List product operation rows

     Returns a list of product operation rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        product_id (Union[Unset, int]):
        operation_id (Union[Unset, int]):
        product_variant_id (Union[Unset, int]):
        operation_name (Union[Unset, str]):
        resource_name (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        product_operation_row_id (Union[Unset, int]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, GetAllProductOperationRowsResponse200]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        product_id=product_id,
        operation_id=operation_id,
        product_variant_id=product_variant_id,
        operation_name=operation_name,
        resource_name=resource_name,
        resource_id=resource_id,
        product_operation_row_id=product_operation_row_id,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    product_id: Unset | int = UNSET,
    operation_id: Unset | int = UNSET,
    product_variant_id: Unset | int = UNSET,
    operation_name: Unset | str = UNSET,
    resource_name: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    product_operation_row_id: Unset | int = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | GetAllProductOperationRowsResponse200 | None:
    """List product operation rows

     Returns a list of product operation rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        product_id (Union[Unset, int]):
        operation_id (Union[Unset, int]):
        product_variant_id (Union[Unset, int]):
        operation_name (Union[Unset, str]):
        resource_name (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        product_operation_row_id (Union[Unset, int]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, GetAllProductOperationRowsResponse200]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            product_id=product_id,
            operation_id=operation_id,
            product_variant_id=product_variant_id,
            operation_name=operation_name,
            resource_name=resource_name,
            resource_id=resource_id,
            product_operation_row_id=product_operation_row_id,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
