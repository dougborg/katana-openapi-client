from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_price_list_customer_request import CreatePriceListCustomerRequest
from ...models.create_price_list_customer_response_400 import (
    CreatePriceListCustomerResponse400,
)
from ...models.create_price_list_customer_response_401 import (
    CreatePriceListCustomerResponse401,
)
from ...models.create_price_list_customer_response_422 import (
    CreatePriceListCustomerResponse422,
)
from ...models.create_price_list_customer_response_429 import (
    CreatePriceListCustomerResponse429,
)
from ...models.create_price_list_customer_response_500 import (
    CreatePriceListCustomerResponse500,
)
from ...models.price_list_customer import PriceListCustomer
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePriceListCustomerRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/price_list_customers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
    | None
):
    if response.status_code == 201:
        response_201 = PriceListCustomer.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CreatePriceListCustomerResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = CreatePriceListCustomerResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePriceListCustomerResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePriceListCustomerResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePriceListCustomerResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
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
    body: CreatePriceListCustomerRequest,
) -> Response[
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
]:
    """Create a price list customer assignment

     Assigns a customer to a price list.

    Args:
        body (CreatePriceListCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListCustomerResponse400, CreatePriceListCustomerResponse401, CreatePriceListCustomerResponse422, CreatePriceListCustomerResponse429, CreatePriceListCustomerResponse500, PriceListCustomer]]
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
    body: CreatePriceListCustomerRequest,
) -> (
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
    | None
):
    """Create a price list customer assignment

     Assigns a customer to a price list.

    Args:
        body (CreatePriceListCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListCustomerResponse400, CreatePriceListCustomerResponse401, CreatePriceListCustomerResponse422, CreatePriceListCustomerResponse429, CreatePriceListCustomerResponse500, PriceListCustomer]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListCustomerRequest,
) -> Response[
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
]:
    """Create a price list customer assignment

     Assigns a customer to a price list.

    Args:
        body (CreatePriceListCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePriceListCustomerResponse400, CreatePriceListCustomerResponse401, CreatePriceListCustomerResponse422, CreatePriceListCustomerResponse429, CreatePriceListCustomerResponse500, PriceListCustomer]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePriceListCustomerRequest,
) -> (
    CreatePriceListCustomerResponse400
    | CreatePriceListCustomerResponse401
    | CreatePriceListCustomerResponse422
    | CreatePriceListCustomerResponse429
    | CreatePriceListCustomerResponse500
    | PriceListCustomer
    | None
):
    """Create a price list customer assignment

     Assigns a customer to a price list.

    Args:
        body (CreatePriceListCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePriceListCustomerResponse400, CreatePriceListCustomerResponse401, CreatePriceListCustomerResponse422, CreatePriceListCustomerResponse429, CreatePriceListCustomerResponse500, PriceListCustomer]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
