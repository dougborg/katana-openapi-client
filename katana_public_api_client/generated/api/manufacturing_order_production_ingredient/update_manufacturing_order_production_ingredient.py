from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.manufacturing_order_production_ingredient_response import (
    ManufacturingOrderProductionIngredientResponse,
)
from ...models.update_manufacturing_order_production_ingredient_request import (
    UpdateManufacturingOrderProductionIngredientRequest,
)
from ...models.update_manufacturing_order_production_ingredient_response_401 import (
    UpdateManufacturingOrderProductionIngredientResponse401,
)
from ...models.update_manufacturing_order_production_ingredient_response_422 import (
    UpdateManufacturingOrderProductionIngredientResponse422,
)
from ...models.update_manufacturing_order_production_ingredient_response_429 import (
    UpdateManufacturingOrderProductionIngredientResponse429,
)
from ...models.update_manufacturing_order_production_ingredient_response_500 import (
    UpdateManufacturingOrderProductionIngredientResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderProductionIngredientRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_production_ingredients/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderProductionIngredientResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = (
            UpdateManufacturingOrderProductionIngredientResponse401.from_dict(
                response.json()
            )
        )

        return response_401
    if response.status_code == 422:
        response_422 = (
            UpdateManufacturingOrderProductionIngredientResponse422.from_dict(
                response.json()
            )
        )

        return response_422
    if response.status_code == 429:
        response_429 = (
            UpdateManufacturingOrderProductionIngredientResponse429.from_dict(
                response.json()
            )
        )

        return response_429
    if response.status_code == 500:
        response_500 = (
            UpdateManufacturingOrderProductionIngredientResponse500.from_dict(
                response.json()
            )
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
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
    body: UpdateManufacturingOrderProductionIngredientRequest,
) -> Response[
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
]:
    """Update a manufacturing order production ingredient

     Updates the specified manufacturing order production ingredient by setting the values of the
    parameters passed.
      Any parameters not provided will be left unchanged. Manufacturing order production ingredient
    cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionIngredientRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderProductionIngredientResponse, UpdateManufacturingOrderProductionIngredientResponse401, UpdateManufacturingOrderProductionIngredientResponse422, UpdateManufacturingOrderProductionIngredientResponse429, UpdateManufacturingOrderProductionIngredientResponse500]]
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
    body: UpdateManufacturingOrderProductionIngredientRequest,
) -> (
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
    | None
):
    """Update a manufacturing order production ingredient

     Updates the specified manufacturing order production ingredient by setting the values of the
    parameters passed.
      Any parameters not provided will be left unchanged. Manufacturing order production ingredient
    cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionIngredientRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderProductionIngredientResponse, UpdateManufacturingOrderProductionIngredientResponse401, UpdateManufacturingOrderProductionIngredientResponse422, UpdateManufacturingOrderProductionIngredientResponse429, UpdateManufacturingOrderProductionIngredientResponse500]
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
    body: UpdateManufacturingOrderProductionIngredientRequest,
) -> Response[
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
]:
    """Update a manufacturing order production ingredient

     Updates the specified manufacturing order production ingredient by setting the values of the
    parameters passed.
      Any parameters not provided will be left unchanged. Manufacturing order production ingredient
    cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionIngredientRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ManufacturingOrderProductionIngredientResponse, UpdateManufacturingOrderProductionIngredientResponse401, UpdateManufacturingOrderProductionIngredientResponse422, UpdateManufacturingOrderProductionIngredientResponse429, UpdateManufacturingOrderProductionIngredientResponse500]]
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
    body: UpdateManufacturingOrderProductionIngredientRequest,
) -> (
    ManufacturingOrderProductionIngredientResponse
    | UpdateManufacturingOrderProductionIngredientResponse401
    | UpdateManufacturingOrderProductionIngredientResponse422
    | UpdateManufacturingOrderProductionIngredientResponse429
    | UpdateManufacturingOrderProductionIngredientResponse500
    | None
):
    """Update a manufacturing order production ingredient

     Updates the specified manufacturing order production ingredient by setting the values of the
    parameters passed.
      Any parameters not provided will be left unchanged. Manufacturing order production ingredient
    cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionIngredientRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ManufacturingOrderProductionIngredientResponse, UpdateManufacturingOrderProductionIngredientResponse401, UpdateManufacturingOrderProductionIngredientResponse422, UpdateManufacturingOrderProductionIngredientResponse429, UpdateManufacturingOrderProductionIngredientResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
