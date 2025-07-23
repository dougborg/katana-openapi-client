from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_sales_return_request import CreateSalesReturnRequest
from ...models.create_sales_return_response_400 import CreateSalesReturnResponse400
from ...models.create_sales_return_response_401 import CreateSalesReturnResponse401
from ...models.create_sales_return_response_422 import CreateSalesReturnResponse422
from ...models.create_sales_return_response_429 import CreateSalesReturnResponse429
from ...models.create_sales_return_response_500 import CreateSalesReturnResponse500
from ...models.sales_return import SalesReturn
from ...types import Response


def _get_kwargs(
    *,
    body: CreateSalesReturnRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_returns",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
    | None
):
    if response.status_code == 201:
        response_201 = SalesReturn.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CreateSalesReturnResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = CreateSalesReturnResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateSalesReturnResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateSalesReturnResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateSalesReturnResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
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
    body: CreateSalesReturnRequest,
) -> Response[
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
]:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSalesReturnResponse400, CreateSalesReturnResponse401, CreateSalesReturnResponse422, CreateSalesReturnResponse429, CreateSalesReturnResponse500, SalesReturn]]
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
    body: CreateSalesReturnRequest,
) -> (
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
    | None
):
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSalesReturnResponse400, CreateSalesReturnResponse401, CreateSalesReturnResponse422, CreateSalesReturnResponse429, CreateSalesReturnResponse500, SalesReturn]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesReturnRequest,
) -> Response[
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
]:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSalesReturnResponse400, CreateSalesReturnResponse401, CreateSalesReturnResponse422, CreateSalesReturnResponse429, CreateSalesReturnResponse500, SalesReturn]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesReturnRequest,
) -> (
    CreateSalesReturnResponse400
    | CreateSalesReturnResponse401
    | CreateSalesReturnResponse422
    | CreateSalesReturnResponse429
    | CreateSalesReturnResponse500
    | SalesReturn
    | None
):
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSalesReturnResponse400, CreateSalesReturnResponse401, CreateSalesReturnResponse422, CreateSalesReturnResponse429, CreateSalesReturnResponse500, SalesReturn]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
