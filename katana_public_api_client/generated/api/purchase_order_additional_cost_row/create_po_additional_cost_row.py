from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_po_additional_cost_row_response_401 import (
    CreatePoAdditionalCostRowResponse401,
)
from ...models.create_po_additional_cost_row_response_422 import (
    CreatePoAdditionalCostRowResponse422,
)
from ...models.create_po_additional_cost_row_response_429 import (
    CreatePoAdditionalCostRowResponse429,
)
from ...models.create_po_additional_cost_row_response_500 import (
    CreatePoAdditionalCostRowResponse500,
)
from ...models.create_purchase_order_additional_cost_row_request import (
    CreatePurchaseOrderAdditionalCostRowRequest,
)
from ...models.purchase_order_additional_cost_row import PurchaseOrderAdditionalCostRow
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePurchaseOrderAdditionalCostRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/po_additional_cost_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderAdditionalCostRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreatePoAdditionalCostRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePoAdditionalCostRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePoAdditionalCostRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePoAdditionalCostRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
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
    body: CreatePurchaseOrderAdditionalCostRowRequest,
) -> Response[
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
]:
    """Create a purchase order additional cost row

     Add a purchase order additional cost row to an existing group.

    Args:
        body (CreatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePoAdditionalCostRowResponse401, CreatePoAdditionalCostRowResponse422, CreatePoAdditionalCostRowResponse429, CreatePoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]]
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
    body: CreatePurchaseOrderAdditionalCostRowRequest,
) -> (
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    """Create a purchase order additional cost row

     Add a purchase order additional cost row to an existing group.

    Args:
        body (CreatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePoAdditionalCostRowResponse401, CreatePoAdditionalCostRowResponse422, CreatePoAdditionalCostRowResponse429, CreatePoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderAdditionalCostRowRequest,
) -> Response[
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
]:
    """Create a purchase order additional cost row

     Add a purchase order additional cost row to an existing group.

    Args:
        body (CreatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePoAdditionalCostRowResponse401, CreatePoAdditionalCostRowResponse422, CreatePoAdditionalCostRowResponse429, CreatePoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderAdditionalCostRowRequest,
) -> (
    CreatePoAdditionalCostRowResponse401
    | CreatePoAdditionalCostRowResponse422
    | CreatePoAdditionalCostRowResponse429
    | CreatePoAdditionalCostRowResponse500
    | PurchaseOrderAdditionalCostRow
    | None
):
    """Create a purchase order additional cost row

     Add a purchase order additional cost row to an existing group.

    Args:
        body (CreatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePoAdditionalCostRowResponse401, CreatePoAdditionalCostRowResponse422, CreatePoAdditionalCostRowResponse429, CreatePoAdditionalCostRowResponse500, PurchaseOrderAdditionalCostRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
