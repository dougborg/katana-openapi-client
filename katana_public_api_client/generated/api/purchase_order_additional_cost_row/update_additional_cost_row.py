from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.purchase_order_additional_cost_row import PurchaseOrderAdditionalCostRow
from ...models.update_additional_cost_row_response_401 import (
    UpdateAdditionalCostRowResponse401,
)
from ...models.update_additional_cost_row_response_422 import (
    UpdateAdditionalCostRowResponse422,
)
from ...models.update_additional_cost_row_response_429 import (
    UpdateAdditionalCostRowResponse429,
)
from ...models.update_additional_cost_row_response_500 import (
    UpdateAdditionalCostRowResponse500,
)
from ...models.update_purchase_order_additional_cost_row_request import (
    UpdatePurchaseOrderAdditionalCostRowRequest,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdatePurchaseOrderAdditionalCostRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/po_additional_cost_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderAdditionalCostRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateAdditionalCostRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = UpdateAdditionalCostRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdateAdditionalCostRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateAdditionalCostRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
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
    body: UpdatePurchaseOrderAdditionalCostRowRequest,
) -> Response[
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
]:
    """Update a purchase order additional cost row

     Updates the specified purchase order additional cost row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[PurchaseOrderAdditionalCostRow, UpdateAdditionalCostRowResponse401, UpdateAdditionalCostRowResponse422, UpdateAdditionalCostRowResponse429, UpdateAdditionalCostRowResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePurchaseOrderAdditionalCostRowRequest,
) -> (
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
    | None
):
    """Update a purchase order additional cost row

     Updates the specified purchase order additional cost row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[PurchaseOrderAdditionalCostRow, UpdateAdditionalCostRowResponse401, UpdateAdditionalCostRowResponse422, UpdateAdditionalCostRowResponse429, UpdateAdditionalCostRowResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePurchaseOrderAdditionalCostRowRequest,
) -> Response[
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
]:
    """Update a purchase order additional cost row

     Updates the specified purchase order additional cost row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[PurchaseOrderAdditionalCostRow, UpdateAdditionalCostRowResponse401, UpdateAdditionalCostRowResponse422, UpdateAdditionalCostRowResponse429, UpdateAdditionalCostRowResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePurchaseOrderAdditionalCostRowRequest,
) -> (
    PurchaseOrderAdditionalCostRow
    | UpdateAdditionalCostRowResponse401
    | UpdateAdditionalCostRowResponse422
    | UpdateAdditionalCostRowResponse429
    | UpdateAdditionalCostRowResponse500
    | None
):
    """Update a purchase order additional cost row

     Updates the specified purchase order additional cost row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderAdditionalCostRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[PurchaseOrderAdditionalCostRow, UpdateAdditionalCostRowResponse401, UpdateAdditionalCostRowResponse422, UpdateAdditionalCostRowResponse429, UpdateAdditionalCostRowResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
