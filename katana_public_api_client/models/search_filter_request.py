from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_filter_request_filter import SearchFilterRequestFilter


T = TypeVar("T", bound="SearchFilterRequest")


@_attrs_define
class SearchFilterRequest:
    """LoopBack-style filter envelope used by POST search endpoints. The
    ``filter`` body supports pagination (``limit`` / ``page`` / ``skip``),
    ordering, and a ``where`` clause with comparison operators
    (``eq`` / ``neq`` / ``gt`` / ``gte`` / ``lt`` / ``lte`` / ``like`` /
    ``ilike`` / ``inq`` / ``nin`` / ``between`` / ``regexp`` / ``exists``)
    plus ``and`` / ``or`` composition. Where clause values are
    intentionally left as free-form because Katana's filter grammar is
    the same regardless of which field is being filtered.

        Example:
            {'filter': {'limit': 50, 'where': {'sales_order_id': {'inq': [1, 2, 3]}}, 'order': 'created_at DESC'}}
    """

    filter_: SearchFilterRequestFilter | Unset = UNSET

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
        from ..models.search_filter_request_filter import SearchFilterRequestFilter

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: SearchFilterRequestFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = SearchFilterRequestFilter.from_dict(_filter_)

        search_filter_request = cls(
            filter_=filter_,
        )

        return search_filter_request
