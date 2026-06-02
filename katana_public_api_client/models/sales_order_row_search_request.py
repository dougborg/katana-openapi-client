from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_row_search_filter import SalesOrderRowSearchFilter


T = TypeVar("T", bound="SalesOrderRowSearchRequest")


@_attrs_define
class SalesOrderRowSearchRequest:
    """Structured filter body for ``POST /sales_order_rows/search``.
    Returns the same paginated ``{"data": [...]}`` shape as
    ``GET /sales_order_rows`` plus an ``X-Pagination`` header. Beta —
    request/response shape may evolve before GA.

        Example:
            {'filter': {'where': {'and': [{'sales_order_id': {'inq': [12345, 12346, 12347]}}, {'quantity': {'gt': 0}},
                {'product_availability': 'IN_STOCK'}]}, 'order': ['delivery_date ASC', 'id ASC'], 'limit': 100, 'page': 1}}

        Attributes:
            filter_ (SalesOrderRowSearchFilter | Unset): Filter envelope for ``POST /sales_order_rows/search``.
    """

    filter_: SalesOrderRowSearchFilter | Unset = UNSET

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
        from ..models.sales_order_row_search_filter import SalesOrderRowSearchFilter

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: SalesOrderRowSearchFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = SalesOrderRowSearchFilter.from_dict(_filter_)

        sales_order_row_search_request = cls(
            filter_=filter_,
        )

        return sales_order_row_search_request
