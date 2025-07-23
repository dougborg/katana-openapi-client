from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.unlink_variant_bin_location_request import (
    UnlinkVariantBinLocationRequest,
)
from ...models.unlink_variant_default_storage_bins_response_401 import (
    UnlinkVariantDefaultStorageBinsResponse401,
)
from ...models.unlink_variant_default_storage_bins_response_422 import (
    UnlinkVariantDefaultStorageBinsResponse422,
)
from ...models.unlink_variant_default_storage_bins_response_429 import (
    UnlinkVariantDefaultStorageBinsResponse429,
)
from ...models.unlink_variant_default_storage_bins_response_500 import (
    UnlinkVariantDefaultStorageBinsResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: list["UnlinkVariantBinLocationRequest"],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/unlink_variant_bin_locations",
    }

    _kwargs["json"] = []
    for componentsschemas_unlink_variant_bin_location_list_request_item_data in body:
        componentsschemas_unlink_variant_bin_location_list_request_item = componentsschemas_unlink_variant_bin_location_list_request_item_data.to_dict()
        _kwargs["json"].append(
            componentsschemas_unlink_variant_bin_location_list_request_item
        )

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = UnlinkVariantDefaultStorageBinsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 422:
        response_422 = UnlinkVariantDefaultStorageBinsResponse422.from_dict(
            response.json()
        )

        return response_422
    if response.status_code == 429:
        response_429 = UnlinkVariantDefaultStorageBinsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = UnlinkVariantDefaultStorageBinsResponse500.from_dict(
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
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
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
    body: list["UnlinkVariantBinLocationRequest"],
) -> Response[
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
]:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UnlinkVariantDefaultStorageBinsResponse401, UnlinkVariantDefaultStorageBinsResponse422, UnlinkVariantDefaultStorageBinsResponse429, UnlinkVariantDefaultStorageBinsResponse500]]
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
    body: list["UnlinkVariantBinLocationRequest"],
) -> (
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
    | None
):
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UnlinkVariantDefaultStorageBinsResponse401, UnlinkVariantDefaultStorageBinsResponse422, UnlinkVariantDefaultStorageBinsResponse429, UnlinkVariantDefaultStorageBinsResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> Response[
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
]:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UnlinkVariantDefaultStorageBinsResponse401, UnlinkVariantDefaultStorageBinsResponse422, UnlinkVariantDefaultStorageBinsResponse429, UnlinkVariantDefaultStorageBinsResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> (
    Any
    | UnlinkVariantDefaultStorageBinsResponse401
    | UnlinkVariantDefaultStorageBinsResponse422
    | UnlinkVariantDefaultStorageBinsResponse429
    | UnlinkVariantDefaultStorageBinsResponse500
    | None
):
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UnlinkVariantDefaultStorageBinsResponse401, UnlinkVariantDefaultStorageBinsResponse422, UnlinkVariantDefaultStorageBinsResponse429, UnlinkVariantDefaultStorageBinsResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
