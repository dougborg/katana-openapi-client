from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_search_request_filter import SalesOrderSearchRequestFilter


T = TypeVar("T", bound="SalesOrderSearchRequest")


@_attrs_define
class SalesOrderSearchRequest:
    """Request payload for searching sales orders with arbitrary filter
    criteria. The ``filter`` object accepts free-form key-value pairs
    — supported keys are documented in the Katana API reference
    (matches POST /sales_orders/search behaviour).

        Example:
            {'filter': {'customer_id': 1501, 'status': 'PACKED'}}
    """

    filter_: SalesOrderSearchRequestFilter | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        filter_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = self.filter_.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if filter_ is not UNSET:
            field_dict["filter"] = filter_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_search_request_filter import (
            SalesOrderSearchRequestFilter,
        )

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: SalesOrderSearchRequestFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = SalesOrderSearchRequestFilter.from_dict(_filter_)

        sales_order_search_request = cls(
            filter_=filter_,
        )

        return sales_order_search_request
