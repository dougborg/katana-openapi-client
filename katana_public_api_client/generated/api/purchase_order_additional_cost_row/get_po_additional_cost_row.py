from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_po_additional_cost_row_response_401 import (
    GetPoAdditionalCostRowResponse401,
)
from ...models.get_po_additional_cost_row_response_429 import (
    GetPoAdditionalCostRowResponse429,
)
from ...models.get_po_additional_cost_row_response_500 import (
    GetPoAdditionalCostRowResponse500,
)
from ...models.purchase_order_additional_cost_row import PurchaseOrderAdditionalCostRow
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/po_additional_cost_rows/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderAdditionalCostRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetPoAdditionalCostRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetPoAdditionalCostRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetPoAdditionalCostRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
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
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
]:
    """Retrieve a purchase order additional cost row

     Retrieves the details of an existing purchase order additional cost row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetPoAdditionalCostRowResponse401, GetPoAdditionalCostRowResponse429, GetPoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]]
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
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    """Retrieve a purchase order additional cost row

     Retrieves the details of an existing purchase order additional cost row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetPoAdditionalCostRowResponse401, GetPoAdditionalCostRowResponse429, GetPoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]
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
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
]:
    """Retrieve a purchase order additional cost row

     Retrieves the details of an existing purchase order additional cost row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetPoAdditionalCostRowResponse401, GetPoAdditionalCostRowResponse429, GetPoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]]
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
    GetPoAdditionalCostRowResponse401
    | GetPoAdditionalCostRowResponse429
    | GetPoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    """Retrieve a purchase order additional cost row

     Retrieves the details of an existing purchase order additional cost row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetPoAdditionalCostRowResponse401, GetPoAdditionalCostRowResponse429, GetPoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
