from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_tax_rate_request import CreateTaxRateRequest
from ...models.create_tax_rate_response_401 import CreateTaxRateResponse401
from ...models.create_tax_rate_response_422 import CreateTaxRateResponse422
from ...models.create_tax_rate_response_429 import CreateTaxRateResponse429
from ...models.create_tax_rate_response_500 import CreateTaxRateResponse500
from ...models.tax_rate import TaxRate
from ...types import Response


def _get_kwargs(
    *,
    body: CreateTaxRateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tax_rates",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
    | None
):
    if response.status_code == 200:
        response_200 = TaxRate.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateTaxRateResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateTaxRateResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateTaxRateResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateTaxRateResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
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
    body: CreateTaxRateRequest,
) -> Response[
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
]:
    """Create a tax rate

     Creates a new tax rate object.

    Args:
        body (CreateTaxRateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateTaxRateResponse401, CreateTaxRateResponse422, CreateTaxRateResponse429, CreateTaxRateResponse500, TaxRate]]
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
    body: CreateTaxRateRequest,
) -> (
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
    | None
):
    """Create a tax rate

     Creates a new tax rate object.

    Args:
        body (CreateTaxRateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateTaxRateResponse401, CreateTaxRateResponse422, CreateTaxRateResponse429, CreateTaxRateResponse500, TaxRate]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateTaxRateRequest,
) -> Response[
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
]:
    """Create a tax rate

     Creates a new tax rate object.

    Args:
        body (CreateTaxRateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateTaxRateResponse401, CreateTaxRateResponse422, CreateTaxRateResponse429, CreateTaxRateResponse500, TaxRate]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateTaxRateRequest,
) -> (
    CreateTaxRateResponse401
    | CreateTaxRateResponse422
    | CreateTaxRateResponse429
    | CreateTaxRateResponse500
    | TaxRate
    | None
):
    """Create a tax rate

     Creates a new tax rate object.

    Args:
        body (CreateTaxRateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateTaxRateResponse401, CreateTaxRateResponse422, CreateTaxRateResponse429, CreateTaxRateResponse500, TaxRate]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
