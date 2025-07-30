from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.manufacturing_order_production import ManufacturingOrderProduction
from ...models.update_manufacturing_order_production_request import (
    UpdateManufacturingOrderProductionRequest,
)
from ...models.update_manufacturing_order_production_response_401 import (
    UpdateManufacturingOrderProductionResponse401,
)
from ...models.update_manufacturing_order_production_response_404 import (
    UpdateManufacturingOrderProductionResponse404,
)
from ...models.update_manufacturing_order_production_response_422 import (
    UpdateManufacturingOrderProductionResponse422,
)
from ...models.update_manufacturing_order_production_response_429 import (
    UpdateManufacturingOrderProductionResponse429,
)
from ...models.update_manufacturing_order_production_response_500 import (
    UpdateManufacturingOrderProductionResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderProductionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_productions/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderProduction.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdateManufacturingOrderProductionResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 404:
        response_404 = UpdateManufacturingOrderProductionResponse404.from_dict(
            response.json()
        )

        return response_404
    if response.status_code == 422:
        response_422 = UpdateManufacturingOrderProductionResponse422.from_dict(
            response.json()
        )

        return response_422
    if response.status_code == 429:
        response_429 = UpdateManufacturingOrderProductionResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = UpdateManufacturingOrderProductionResponse500.from_dict(
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
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
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
    body: UpdateManufacturingOrderProductionRequest,
) -> Response[
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
]:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderProduction, UpdateManufacturingOrderProductionResponse401, UpdateManufacturingOrderProductionResponse404, UpdateManufacturingOrderProductionResponse422, UpdateManufacturingOrderProductionResponse429, UpdateManufacturingOrderProductionResponse500]]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> (
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
    | None
):
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderProduction, UpdateManufacturingOrderProductionResponse401, UpdateManufacturingOrderProductionResponse404, UpdateManufacturingOrderProductionResponse422, UpdateManufacturingOrderProductionResponse429, UpdateManufacturingOrderProductionResponse500]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> Response[
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
]:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderProduction, UpdateManufacturingOrderProductionResponse401, UpdateManufacturingOrderProductionResponse404, UpdateManufacturingOrderProductionResponse422, UpdateManufacturingOrderProductionResponse429, UpdateManufacturingOrderProductionResponse500]]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> (
    ManufacturingOrderProduction
    | UpdateManufacturingOrderProductionResponse401
    | UpdateManufacturingOrderProductionResponse404
    | UpdateManufacturingOrderProductionResponse422
    | UpdateManufacturingOrderProductionResponse429
    | UpdateManufacturingOrderProductionResponse500
    | None
):
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderProduction, UpdateManufacturingOrderProductionResponse401, UpdateManufacturingOrderProductionResponse404, UpdateManufacturingOrderProductionResponse422, UpdateManufacturingOrderProductionResponse429, UpdateManufacturingOrderProductionResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
