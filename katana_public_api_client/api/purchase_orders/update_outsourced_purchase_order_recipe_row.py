from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.outsourced_purchase_order_recipe_row import (
    OutsourcedPurchaseOrderRecipeRow,
)
from ...models.update_outsourced_purchase_order_recipe_row_body import (
    UpdateOutsourcedPurchaseOrderRecipeRowBody,
)


def _get_kwargs(
    id: int,
    *,
    body: UpdateOutsourcedPurchaseOrderRecipeRowBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/outsourced_purchase_order_recipe_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow | None:
    if response.status_code == 200:
        response_200 = OutsourcedPurchaseOrderRecipeRow.from_dict(response.json())

        return response_200

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
) -> Response[DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow]:
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
    body: UpdateOutsourcedPurchaseOrderRecipeRowBody,
) -> Response[DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow]:
    """Update an outsourced purchase order recipe row

     Updates an outsourced purchase order recipe row.

    Args:
        id (int):
        body (UpdateOutsourcedPurchaseOrderRecipeRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, OutsourcedPurchaseOrderRecipeRow]]
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
    body: UpdateOutsourcedPurchaseOrderRecipeRowBody,
) -> DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow | None:
    """Update an outsourced purchase order recipe row

     Updates an outsourced purchase order recipe row.

    Args:
        id (int):
        body (UpdateOutsourcedPurchaseOrderRecipeRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, OutsourcedPurchaseOrderRecipeRow]
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
    body: UpdateOutsourcedPurchaseOrderRecipeRowBody,
) -> Response[DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow]:
    """Update an outsourced purchase order recipe row

     Updates an outsourced purchase order recipe row.

    Args:
        id (int):
        body (UpdateOutsourcedPurchaseOrderRecipeRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, OutsourcedPurchaseOrderRecipeRow]]
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
    body: UpdateOutsourcedPurchaseOrderRecipeRowBody,
) -> DetailedErrorResponse | ErrorResponse | OutsourcedPurchaseOrderRecipeRow | None:
    """Update an outsourced purchase order recipe row

     Updates an outsourced purchase order recipe row.

    Args:
        id (int):
        body (UpdateOutsourcedPurchaseOrderRecipeRowBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, OutsourcedPurchaseOrderRecipeRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
