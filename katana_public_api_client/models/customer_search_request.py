from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.customer_search_filter import CustomerSearchFilter


T = TypeVar("T", bound="CustomerSearchRequest")


@_attrs_define
class CustomerSearchRequest:
    """Structured search body for ``POST /customers/search``. Returns the
    same paginated ``{"data": [...]}`` shape as the corresponding list
    endpoint, plus an ``X-Pagination`` header.

        Example:
            {'filter': {'and': [{'category': None, 'eq': 'Wholesale'}]}, 'order': ['name ASC'], 'limit': 50, 'page': 1}

        Attributes:
            filter_ (CustomerSearchFilter | Unset): Filter clause for ``POST /customers/search``. Only the fields listed
                here may appear; unknown fields are rejected with 422. Custom field
                values are addressable via ``custom_fields.<uuid>`` keys.
            order (list[str] | str | Unset): Sort directive(s). Each entry is ``<field> ASC|DESC``
                (direction defaults to ASC). Only filterable fields may be
                used; ``custom_fields.<uuid>`` paths are orderable.
            limit (int | Unset): Page size; maximum 200. Omit to let the server apply its
                default of 50.
            page (int | Unset): 1-based page number. Omit to let the server default to 1.
    """

    filter_: CustomerSearchFilter | Unset = UNSET
    order: list[str] | str | Unset = UNSET
    limit: int | Unset = UNSET
    page: int | Unset = UNSET

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_search_filter import (
            CustomerSearchFilter,
        )

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: CustomerSearchFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = CustomerSearchFilter.from_dict(_filter_)

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

        customer_search_request = cls(
            filter_=filter_,
            order=order,
            limit=limit,
            page=page,
        )

        return customer_search_request
