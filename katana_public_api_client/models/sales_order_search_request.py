from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_search_filter import SalesOrderSearchFilter


T = TypeVar("T", bound="SalesOrderSearchRequest")


@_attrs_define
class SalesOrderSearchRequest:
    """Structured filter body for ``POST /sales_orders/search``. Returns
    the same paginated ``{"data": [...]}`` shape as
    ``GET /sales_orders`` plus an ``X-Pagination`` header. Beta —
    request/response shape may evolve before GA.

        Example:
            {'filter': {'where': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}}, {'created_at': {'gte':
                '2026-01-01T00:00:00.000Z'}}, {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at
                DESC', 'id DESC'], 'limit': 50, 'page': 1}}

        Attributes:
            filter_ (SalesOrderSearchFilter | Unset): Filter envelope for ``POST /sales_orders/search``.
    """

    filter_: SalesOrderSearchFilter | Unset = UNSET

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
        from ..models.sales_order_search_filter import SalesOrderSearchFilter

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: SalesOrderSearchFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = SalesOrderSearchFilter.from_dict(_filter_)

        sales_order_search_request = cls(
            filter_=filter_,
        )

        return sales_order_search_request
