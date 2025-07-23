from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_service_response_401 import DeleteServiceResponse401
from ...models.delete_service_response_404 import DeleteServiceResponse404
from ...models.delete_service_response_429 import DeleteServiceResponse429
from ...models.delete_service_response_500 import DeleteServiceResponse500
from ...types import Response


def _get_kwargs(
    service_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/services/{service_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = DeleteServiceResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteServiceResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteServiceResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteServiceResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
]:
    """Delete Service

     Delete a Service by its ID. (See: [Delete
    Service](https://developer.katanamrp.com/reference/deleteservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteServiceResponse401, DeleteServiceResponse404, DeleteServiceResponse429, DeleteServiceResponse500]]
    """

    kwargs = _get_kwargs(
        service_id=service_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
    | None
):
    """Delete Service

     Delete a Service by its ID. (See: [Delete
    Service](https://developer.katanamrp.com/reference/deleteservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteServiceResponse401, DeleteServiceResponse404, DeleteServiceResponse429, DeleteServiceResponse500]
    """

    return sync_detailed(
        service_id=service_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
]:
    """Delete Service

     Delete a Service by its ID. (See: [Delete
    Service](https://developer.katanamrp.com/reference/deleteservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteServiceResponse401, DeleteServiceResponse404, DeleteServiceResponse429, DeleteServiceResponse500]]
    """

    kwargs = _get_kwargs(
        service_id=service_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteServiceResponse401
    | DeleteServiceResponse404
    | DeleteServiceResponse429
    | DeleteServiceResponse500
    | None
):
    """Delete Service

     Delete a Service by its ID. (See: [Delete
    Service](https://developer.katanamrp.com/reference/deleteservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteServiceResponse401, DeleteServiceResponse404, DeleteServiceResponse429, DeleteServiceResponse500]
    """

    return (
        await asyncio_detailed(
            service_id=service_id,
            client=client,
        )
    ).parsed
