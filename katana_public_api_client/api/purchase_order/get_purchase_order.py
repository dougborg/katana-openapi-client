from http import HTTPStatus
from typing import Any, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_purchase_order_extend_item import GetPurchaseOrderExtendItem
from ...models.outsourced_purchase_order import OutsourcedPurchaseOrder
from ...models.regular_purchase_order import RegularPurchaseOrder


def _get_kwargs(
    id: int,
    *,
    extend: Unset | list[GetPurchaseOrderExtendItem] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/purchase_orders/{id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"] | None:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_purchase_order_type_0 = (
                    RegularPurchaseOrder.from_dict(data)
                )

                return componentsschemas_purchase_order_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_purchase_order_type_1 = OutsourcedPurchaseOrder.from_dict(
                data
            )

            return componentsschemas_purchase_order_type_1

        response_200 = _parse_response_200(response.json())

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
) -> Response[ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]]:
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
    extend: Unset | list[GetPurchaseOrderExtendItem] = UNSET,
) -> Response[ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]]:
    """Retrieve a purchase order

     Retrieves the details of an existing purchase order based on ID

    Args:
        id (int):
        extend (Union[Unset, list[GetPurchaseOrderExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
    """

    kwargs = _get_kwargs(
        id=id,
        extend=extend,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetPurchaseOrderExtendItem] = UNSET,
) -> ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"] | None:
    """Retrieve a purchase order

     Retrieves the details of an existing purchase order based on ID

    Args:
        id (int):
        extend (Union[Unset, list[GetPurchaseOrderExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
    """

    return sync_detailed(
        id=id,
        client=client,
        extend=extend,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetPurchaseOrderExtendItem] = UNSET,
) -> Response[ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]]:
    """Retrieve a purchase order

     Retrieves the details of an existing purchase order based on ID

    Args:
        id (int):
        extend (Union[Unset, list[GetPurchaseOrderExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
    """

    kwargs = _get_kwargs(
        id=id,
        extend=extend,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    extend: Unset | list[GetPurchaseOrderExtendItem] = UNSET,
) -> ErrorResponse | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"] | None:
    """Retrieve a purchase order

     Retrieves the details of an existing purchase order based on ID

    Args:
        id (int):
        extend (Union[Unset, list[GetPurchaseOrderExtendItem]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            extend=extend,
        )
    ).parsed
