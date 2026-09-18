from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.variant_search_request_include_item import VariantSearchRequestIncludeItem

if TYPE_CHECKING:
    from ..models.variant_search_filter import VariantSearchFilter


T = TypeVar("T", bound="VariantSearchRequest")


@_attrs_define
class VariantSearchRequest:
    """Structured search body for ``POST /variants/search``. Returns the
    same paginated ``{"data": [...]}`` shape as the corresponding list
    endpoint, plus an ``X-Pagination`` header.

        Example:
            {'filter': {'and': [{'item_type': None, 'eq': 'product'}]}, 'order': ['sku ASC'], 'limit': 50, 'page': 1}

        Attributes:
            filter_ (VariantSearchFilter | Unset): Filter clause for ``POST /variants/search``. Only the fields listed
                here may appear; unknown fields are rejected with 422. Custom field
                values are addressable via ``custom_fields.<uuid>`` keys.
            order (list[str] | str | Unset): Sort directive(s). Each entry is ``<field> ASC|DESC``
                (direction defaults to ASC). Only filterable fields may be
                used; ``custom_fields.<uuid>`` paths are orderable.
            limit (int | Unset): Page size; maximum 200. Omit to let the server apply its
                default of 50.
            page (int | Unset): 1-based page number. Omit to let the server default to 1.
            include (list[VariantSearchRequestIncludeItem] | Unset): Related data to include, and result-set widening.
                ``item``
                enriches each variant with its parent item under ``item``;
                ``archived`` and ``deleted`` include otherwise-excluded
                variants in the results.
    """

    filter_: VariantSearchFilter | Unset = UNSET
    order: list[str] | str | Unset = UNSET
    limit: int | Unset = UNSET
    page: int | Unset = UNSET
    include: list[VariantSearchRequestIncludeItem] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        filter_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = self.filter_.to_dict()

        order: list[str] | str | Unset
        if isinstance(self.order, Unset):
            order = UNSET
        elif isinstance(self.order, list):
            order = self.order

        else:
            order = self.order

        limit = self.limit

        page = self.page

        include: list[str] | Unset = UNSET
        if not isinstance(self.include, Unset):
            include = []
            for include_item_data in self.include:
                include_item = include_item_data.value
                include.append(include_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if order is not UNSET:
            field_dict["order"] = order
        if limit is not UNSET:
            field_dict["limit"] = limit
        if page is not UNSET:
            field_dict["page"] = page
        if include is not UNSET:
            field_dict["include"] = include

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.variant_search_filter import VariantSearchFilter

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: VariantSearchFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = VariantSearchFilter.from_dict(_filter_)

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

        _include = d.pop("include", UNSET)
        include: list[VariantSearchRequestIncludeItem] | Unset = UNSET
        if _include is not UNSET:
            include = []
            for include_item_data in _include:
                include_item = VariantSearchRequestIncludeItem(include_item_data)

                include.append(include_item)

        variant_search_request = cls(
            filter_=filter_,
            order=order,
            limit=limit,
            page=page,
            include=include,
        )

        return variant_search_request
