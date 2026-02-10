from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response
from ...models.demand_forecast_response import DemandForecastResponse
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    variant_id: int,
    location_id: int,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["variant_id"] = variant_id

    params["location_id"] = location_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/demand_forecasts",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DemandForecastResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = DemandForecastResponse.from_dict(response.json())

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
) -> Response[DemandForecastResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    variant_id: int,
    location_id: int,
) -> Response[DemandForecastResponse | ErrorResponse]:
    """List planned demand forecast for variant in location

     Returns planned forecasted demand for a variant in given location.

    Args:
        variant_id (int):
        location_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DemandForecastResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        variant_id=variant_id,
        location_id=location_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    variant_id: int,
    location_id: int,
) -> DemandForecastResponse | ErrorResponse | None:
    """List planned demand forecast for variant in location

     Returns planned forecasted demand for a variant in given location.

    Args:
        variant_id (int):
        location_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DemandForecastResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        variant_id=variant_id,
        location_id=location_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    variant_id: int,
    location_id: int,
) -> Response[DemandForecastResponse | ErrorResponse]:
    """List planned demand forecast for variant in location

     Returns planned forecasted demand for a variant in given location.

    Args:
        variant_id (int):
        location_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DemandForecastResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        variant_id=variant_id,
        location_id=location_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    variant_id: int,
    location_id: int,
) -> DemandForecastResponse | ErrorResponse | None:
    """List planned demand forecast for variant in location

     Returns planned forecasted demand for a variant in given location.

    Args:
        variant_id (int):
        location_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DemandForecastResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            variant_id=variant_id,
            location_id=location_id,
        )
    ).parsed
