import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_manufacturing_order_operation_rows_response_401 import (
    GetAllManufacturingOrderOperationRowsResponse401,
)
from ...models.get_all_manufacturing_order_operation_rows_response_429 import (
    GetAllManufacturingOrderOperationRowsResponse429,
)
from ...models.get_all_manufacturing_order_operation_rows_response_500 import (
    GetAllManufacturingOrderOperationRowsResponse500,
)
from ...models.get_all_manufacturing_order_operation_rows_status import (
    GetAllManufacturingOrderOperationRowsStatus,
)
from ...models.manufacturing_order_operation_row_list_response import (
    ManufacturingOrderOperationRowListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    status: Unset | GetAllManufacturingOrderOperationRowsStatus = UNSET,
    manufacturing_order_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params["manufacturing_order_id"] = manufacturing_order_id

    params["limit"] = limit

    params["page"] = page

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

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/manufacturing_order_operation_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderOperationRowListResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = GetAllManufacturingOrderOperationRowsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetAllManufacturingOrderOperationRowsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetAllManufacturingOrderOperationRowsResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
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
    ids: Unset | list[int] = UNSET,
    status: Unset | GetAllManufacturingOrderOperationRowsStatus = UNSET,
    manufacturing_order_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
]:
    """List all manufacturing order operation rows

     Returns a list of manufacturing order operation rows you've previously created.
      The manufacturing order operation rows are returned in sorted order,
       with the most recent manufacturing order operation rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        status (Union[Unset, GetAllManufacturingOrderOperationRowsStatus]):
        manufacturing_order_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllManufacturingOrderOperationRowsResponse401, GetAllManufacturingOrderOperationRowsResponse429, GetAllManufacturingOrderOperationRowsResponse500, ManufacturingOrderOperationRowListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        status=status,
        manufacturing_order_id=manufacturing_order_id,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    status: Unset | GetAllManufacturingOrderOperationRowsStatus = UNSET,
    manufacturing_order_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
    | None
):
    """List all manufacturing order operation rows

     Returns a list of manufacturing order operation rows you've previously created.
      The manufacturing order operation rows are returned in sorted order,
       with the most recent manufacturing order operation rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        status (Union[Unset, GetAllManufacturingOrderOperationRowsStatus]):
        manufacturing_order_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllManufacturingOrderOperationRowsResponse401, GetAllManufacturingOrderOperationRowsResponse429, GetAllManufacturingOrderOperationRowsResponse500, ManufacturingOrderOperationRowListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        status=status,
        manufacturing_order_id=manufacturing_order_id,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    status: Unset | GetAllManufacturingOrderOperationRowsStatus = UNSET,
    manufacturing_order_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
]:
    """List all manufacturing order operation rows

     Returns a list of manufacturing order operation rows you've previously created.
      The manufacturing order operation rows are returned in sorted order,
       with the most recent manufacturing order operation rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        status (Union[Unset, GetAllManufacturingOrderOperationRowsStatus]):
        manufacturing_order_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllManufacturingOrderOperationRowsResponse401, GetAllManufacturingOrderOperationRowsResponse429, GetAllManufacturingOrderOperationRowsResponse500, ManufacturingOrderOperationRowListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        status=status,
        manufacturing_order_id=manufacturing_order_id,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    status: Unset | GetAllManufacturingOrderOperationRowsStatus = UNSET,
    manufacturing_order_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllManufacturingOrderOperationRowsResponse401
    | GetAllManufacturingOrderOperationRowsResponse429
    | GetAllManufacturingOrderOperationRowsResponse500
    | ManufacturingOrderOperationRowListResponse
    | None
):
    """List all manufacturing order operation rows

     Returns a list of manufacturing order operation rows you've previously created.
      The manufacturing order operation rows are returned in sorted order,
       with the most recent manufacturing order operation rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        status (Union[Unset, GetAllManufacturingOrderOperationRowsStatus]):
        manufacturing_order_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllManufacturingOrderOperationRowsResponse401, GetAllManufacturingOrderOperationRowsResponse429, GetAllManufacturingOrderOperationRowsResponse500, ManufacturingOrderOperationRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            status=status,
            manufacturing_order_id=manufacturing_order_id,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            include_deleted=include_deleted,
        )
    ).parsed
