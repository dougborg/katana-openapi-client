from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_filter_request_filter_where import (
        SearchFilterRequestFilterWhere,
    )


T = TypeVar("T", bound="SearchFilterRequestFilter")


@_attrs_define
class SearchFilterRequestFilter:
    limit: int | Unset = UNSET
    page: int | Unset = UNSET
    skip: int | Unset = UNSET
    order: list[str] | str | Unset = UNSET
    where: SearchFilterRequestFilterWhere | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        limit = self.limit

        page = self.page

        skip = self.skip

        order: list[str] | str | Unset
        if isinstance(self.order, Unset):
            order = UNSET
        elif isinstance(self.order, list):
            order = self.order

        else:
            order = self.order

        where: dict[str, Any] | Unset = UNSET
        if not isinstance(self.where, Unset):
            where = self.where.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if limit is not UNSET:
            field_dict["limit"] = limit
        if page is not UNSET:
            field_dict["page"] = page
        if skip is not UNSET:
            field_dict["skip"] = skip
        if order is not UNSET:
            field_dict["order"] = order
        if where is not UNSET:
            field_dict["where"] = where

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_filter_request_filter_where import (
            SearchFilterRequestFilterWhere,
        )

        d = dict(src_dict)
        limit = d.pop("limit", UNSET)

        page = d.pop("page", UNSET)

        skip = d.pop("skip", UNSET)

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

        _where = d.pop("where", UNSET)
        where: SearchFilterRequestFilterWhere | Unset
        if isinstance(_where, Unset):
            where = UNSET
        else:
            where = SearchFilterRequestFilterWhere.from_dict(_where)

        search_filter_request_filter = cls(
            limit=limit,
            page=page,
            skip=skip,
            order=order,
            where=where,
        )

        return search_filter_request_filter
