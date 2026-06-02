from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_row_search_where import SalesOrderRowSearchWhere


T = TypeVar("T", bound="SalesOrderRowSearchFilter")


@_attrs_define
class SalesOrderRowSearchFilter:
    """Filter envelope for ``POST /sales_order_rows/search``."""

    where: SalesOrderRowSearchWhere | Unset = UNSET
    order: list[str] | str | Unset = UNSET
    limit: int | Unset = UNSET
    page: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        where: dict[str, Any] | Unset = UNSET
        if not isinstance(self.where, Unset):
            where = self.where.to_dict()

        order: list[str] | str | Unset
        if isinstance(self.order, Unset):
            order = UNSET
        elif isinstance(self.order, list):
            order = self.order

        else:
            order = self.order

        limit = self.limit

        page = self.page

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if where is not UNSET:
            field_dict["where"] = where
        if order is not UNSET:
            field_dict["order"] = order
        if limit is not UNSET:
            field_dict["limit"] = limit
        if page is not UNSET:
            field_dict["page"] = page

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_row_search_where import SalesOrderRowSearchWhere

        d = dict(src_dict)
        _where = d.pop("where", UNSET)
        where: SalesOrderRowSearchWhere | Unset
        if isinstance(_where, Unset):
            where = UNSET
        else:
            where = SalesOrderRowSearchWhere.from_dict(_where)

        def _parse_order(data: object) -> list[str] | str | Unset:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                order_type_1 = cast(list[str], data)

                return order_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | str | Unset, data)

        order = _parse_order(d.pop("order", UNSET))

        limit = d.pop("limit", UNSET)

        page = d.pop("page", UNSET)

        sales_order_row_search_filter = cls(
            where=where,
            order=order,
            limit=limit,
            page=page,
        )

        return sales_order_row_search_filter
