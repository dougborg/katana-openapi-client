from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

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
            {'filter': {'and': [{'status': {'inq': ['NOT_SHIPPED', 'PACKED']}}, {'created_at': {'gte':
                '2026-01-01T00:00:00.000Z'}}, {'custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef': 2}]}, 'order': ['created_at
                DESC', 'id DESC'], 'limit': 50, 'page': 1}

        Attributes:
            filter_ (SalesOrderSearchFilter | Unset): ``filter`` clause for ``POST /sales_orders/search``. Only the fields
                listed here may appear; unknown fields are rejected with 422.
                Custom field values are addressable via additional
                ``custom_fields.<uuid>`` keys (snake_case, matching the
                request/response body), where ``<uuid>`` is the custom field
                definition id — its value is a bare value or a ``SearchComparator``
                like any other predicate (for ``singleSelect`` the value is the
                integer choice ``id``). Compose with ``and`` / ``or`` (max nesting
                depth 2).
            order (list[str] | str | Unset): Sort directive(s). Each entry is ``<field> ASC|DESC``
                (direction defaults to ASC). Only filterable fields may be
                used; ``custom_fields.<uuid>`` paths are orderable.
            limit (int | Unset): Page size; maximum 200. Omit to let the server apply its
                default of 50 (the client omits the key when unset rather than
                sending a default, so direct construction and round-tripped
                ``from_dict`` payloads behave identically).
            page (int | Unset): 1-based page number. Omit to let the server default to 1.
    """

    filter_: SalesOrderSearchFilter | Unset = UNSET
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
        from ..models.sales_order_search_filter import (
            SalesOrderSearchFilter,
        )

        d = dict(src_dict)
        _filter_ = d.pop("filter", UNSET)
        filter_: SalesOrderSearchFilter | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = SalesOrderSearchFilter.from_dict(_filter_)

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

        sales_order_search_request = cls(
            filter_=filter_,
            order=order,
            limit=limit,
            page=page,
        )

        return sales_order_search_request
