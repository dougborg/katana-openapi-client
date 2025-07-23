from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_operators_response_401 import GetAllOperatorsResponse401
from ...models.get_all_operators_response_429 import GetAllOperatorsResponse429
from ...models.get_all_operators_response_500 import GetAllOperatorsResponse500
from ...models.operator_list_response import OperatorListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    working_area: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["working_area"] = working_area

    params["resource_id"] = resource_id

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/operators",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
    | None
):
    if response.status_code == 200:
        response_200 = OperatorListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllOperatorsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllOperatorsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllOperatorsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
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
    working_area: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
]:
    """Get all operators

     Retrieves a list of operators based on the provided filters.

    Args:
        working_area (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllOperatorsResponse401, GetAllOperatorsResponse429, GetAllOperatorsResponse500, OperatorListResponse]]
    """

    kwargs = _get_kwargs(
        working_area=working_area,
        resource_id=resource_id,
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    working_area: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
    | None
):
    """Get all operators

     Retrieves a list of operators based on the provided filters.

    Args:
        working_area (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllOperatorsResponse401, GetAllOperatorsResponse429, GetAllOperatorsResponse500, OperatorListResponse]
    """

    return sync_detailed(
        client=client,
        working_area=working_area,
        resource_id=resource_id,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    working_area: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
]:
    """Get all operators

     Retrieves a list of operators based on the provided filters.

    Args:
        working_area (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllOperatorsResponse401, GetAllOperatorsResponse429, GetAllOperatorsResponse500, OperatorListResponse]]
    """

    kwargs = _get_kwargs(
        working_area=working_area,
        resource_id=resource_id,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    working_area: Unset | str = UNSET,
    resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllOperatorsResponse401
    | GetAllOperatorsResponse429
    | GetAllOperatorsResponse500
    | OperatorListResponse
    | None
):
    """Get all operators

     Retrieves a list of operators based on the provided filters.

    Args:
        working_area (Union[Unset, str]):
        resource_id (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllOperatorsResponse401, GetAllOperatorsResponse429, GetAllOperatorsResponse500, OperatorListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            working_area=working_area,
            resource_id=resource_id,
            limit=limit,
            page=page,
        )
    ).parsed
