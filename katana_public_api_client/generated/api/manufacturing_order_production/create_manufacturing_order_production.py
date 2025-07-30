from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_production_request import (
    CreateManufacturingOrderProductionRequest,
)
from ...models.create_manufacturing_order_production_response_401 import (
    CreateManufacturingOrderProductionResponse401,
)
from ...models.create_manufacturing_order_production_response_429 import (
    CreateManufacturingOrderProductionResponse429,
)
from ...models.create_manufacturing_order_production_response_500 import (
    CreateManufacturingOrderProductionResponse500,
)
from ...models.manufacturing_order_production import ManufacturingOrderProduction
from ...types import Response


def _get_kwargs(
    *,
    body: CreateManufacturingOrderProductionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_productions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderProduction.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateManufacturingOrderProductionResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = CreateManufacturingOrderProductionResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = CreateManufacturingOrderProductionResponse500.from_dict(
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
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
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
    body: CreateManufacturingOrderProductionRequest,
) -> Response[
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
]:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderProductionResponse401, CreateManufacturingOrderProductionResponse429, CreateManufacturingOrderProductionResponse500, ManufacturingOrderProduction]]
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
    body: CreateManufacturingOrderProductionRequest,
) -> (
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderProductionResponse401, CreateManufacturingOrderProductionResponse429, CreateManufacturingOrderProductionResponse500, ManufacturingOrderProduction]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderProductionRequest,
) -> Response[
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
]:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderProductionResponse401, CreateManufacturingOrderProductionResponse429, CreateManufacturingOrderProductionResponse500, ManufacturingOrderProduction]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderProductionRequest,
) -> (
    CreateManufacturingOrderProductionResponse401
    | CreateManufacturingOrderProductionResponse429
    | CreateManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderProductionResponse401, CreateManufacturingOrderProductionResponse429, CreateManufacturingOrderProductionResponse500, ManufacturingOrderProduction]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
