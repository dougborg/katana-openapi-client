from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_search_where_and_item import SalesOrderSearchWhereAndItem
    from ..models.sales_order_search_where_or_item import SalesOrderSearchWhereOrItem
    from ..models.search_comparator import SearchComparator


T = TypeVar("T", bound="SalesOrderSearchWhere")


@_attrs_define
class SalesOrderSearchWhere:
    """``where`` clause for ``POST /sales_orders/search``. Only the fields
    listed here may appear; unknown fields are rejected with 422.
    Custom field values are addressable via additional
    ``custom_fields.<uuid>`` keys (snake_case, matching the
    request/response body), where ``<uuid>`` is the custom field
    definition id — its value is a bare value or a ``SearchComparator``
    like any other predicate (for ``singleSelect`` the value is the
    integer choice ``id``). Compose with ``and`` / ``or`` (max nesting
    depth 2).
    """

    and_: list[SalesOrderSearchWhereAndItem] | Unset = UNSET
    or_: list[SalesOrderSearchWhereOrItem] | Unset = UNSET
    id: bool | float | None | SearchComparator | str | Unset = UNSET
    order_no: bool | float | None | SearchComparator | str | Unset = UNSET
    customer_id: bool | float | None | SearchComparator | str | Unset = UNSET
    customer_ref: bool | float | None | SearchComparator | str | Unset = UNSET
    location_id: bool | float | None | SearchComparator | str | Unset = UNSET
    status: bool | float | None | SearchComparator | str | Unset = UNSET
    invoicing_status: bool | float | None | SearchComparator | str | Unset = UNSET
    production_status: bool | float | None | SearchComparator | str | Unset = UNSET
    source: bool | float | None | SearchComparator | str | Unset = UNSET
    currency: bool | float | None | SearchComparator | str | Unset = UNSET
    product_availability: bool | float | None | SearchComparator | str | Unset = UNSET
    ingredient_availability: bool | float | None | SearchComparator | str | Unset = (
        UNSET
    )
    ecommerce_order_type: bool | float | None | SearchComparator | str | Unset = UNSET
    ecommerce_store_name: bool | float | None | SearchComparator | str | Unset = UNSET
    ecommerce_order_id: bool | float | None | SearchComparator | str | Unset = UNSET
    tracking_number: bool | float | None | SearchComparator | str | Unset = UNSET
    created_at: bool | float | None | SearchComparator | str | Unset = UNSET
    updated_at: bool | float | None | SearchComparator | str | Unset = UNSET
    order_created_date: bool | float | None | SearchComparator | str | Unset = UNSET
    delivery_date: bool | float | None | SearchComparator | str | Unset = UNSET
    picked_date: bool | float | None | SearchComparator | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.search_comparator import SearchComparator

        and_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.and_, Unset):
            and_ = []
            for and_item_data in self.and_:
                and_item = and_item_data.to_dict()
                and_.append(and_item)

        or_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.or_, Unset):
            or_ = []
            for or_item_data in self.or_:
                or_item = or_item_data.to_dict()
                or_.append(or_item)

        id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, SearchComparator):
            id = self.id.to_dict()
        else:
            id = self.id

        order_no: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.order_no, Unset):
            order_no = UNSET
        elif isinstance(self.order_no, SearchComparator):
            order_no = self.order_no.to_dict()
        else:
            order_no = self.order_no

        customer_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.customer_id, Unset):
            customer_id = UNSET
        elif isinstance(self.customer_id, SearchComparator):
            customer_id = self.customer_id.to_dict()
        else:
            customer_id = self.customer_id

        customer_ref: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.customer_ref, Unset):
            customer_ref = UNSET
        elif isinstance(self.customer_ref, SearchComparator):
            customer_ref = self.customer_ref.to_dict()
        else:
            customer_ref = self.customer_ref

        location_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.location_id, Unset):
            location_id = UNSET
        elif isinstance(self.location_id, SearchComparator):
            location_id = self.location_id.to_dict()
        else:
            location_id = self.location_id

        status: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, SearchComparator):
            status = self.status.to_dict()
        else:
            status = self.status

        invoicing_status: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.invoicing_status, Unset):
            invoicing_status = UNSET
        elif isinstance(self.invoicing_status, SearchComparator):
            invoicing_status = self.invoicing_status.to_dict()
        else:
            invoicing_status = self.invoicing_status

        production_status: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.production_status, Unset):
            production_status = UNSET
        elif isinstance(self.production_status, SearchComparator):
            production_status = self.production_status.to_dict()
        else:
            production_status = self.production_status

        source: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        elif isinstance(self.source, SearchComparator):
            source = self.source.to_dict()
        else:
            source = self.source

        currency: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        elif isinstance(self.currency, SearchComparator):
            currency = self.currency.to_dict()
        else:
            currency = self.currency

        product_availability: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.product_availability, Unset):
            product_availability = UNSET
        elif isinstance(self.product_availability, SearchComparator):
            product_availability = self.product_availability.to_dict()
        else:
            product_availability = self.product_availability

        ingredient_availability: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.ingredient_availability, Unset):
            ingredient_availability = UNSET
        elif isinstance(self.ingredient_availability, SearchComparator):
            ingredient_availability = self.ingredient_availability.to_dict()
        else:
            ingredient_availability = self.ingredient_availability

        ecommerce_order_type: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.ecommerce_order_type, Unset):
            ecommerce_order_type = UNSET
        elif isinstance(self.ecommerce_order_type, SearchComparator):
            ecommerce_order_type = self.ecommerce_order_type.to_dict()
        else:
            ecommerce_order_type = self.ecommerce_order_type

        ecommerce_store_name: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.ecommerce_store_name, Unset):
            ecommerce_store_name = UNSET
        elif isinstance(self.ecommerce_store_name, SearchComparator):
            ecommerce_store_name = self.ecommerce_store_name.to_dict()
        else:
            ecommerce_store_name = self.ecommerce_store_name

        ecommerce_order_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.ecommerce_order_id, Unset):
            ecommerce_order_id = UNSET
        elif isinstance(self.ecommerce_order_id, SearchComparator):
            ecommerce_order_id = self.ecommerce_order_id.to_dict()
        else:
            ecommerce_order_id = self.ecommerce_order_id

        tracking_number: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        elif isinstance(self.tracking_number, SearchComparator):
            tracking_number = self.tracking_number.to_dict()
        else:
            tracking_number = self.tracking_number

        created_at: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, SearchComparator):
            created_at = self.created_at.to_dict()
        else:
            created_at = self.created_at

        updated_at: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, SearchComparator):
            updated_at = self.updated_at.to_dict()
        else:
            updated_at = self.updated_at

        order_created_date: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.order_created_date, Unset):
            order_created_date = UNSET
        elif isinstance(self.order_created_date, SearchComparator):
            order_created_date = self.order_created_date.to_dict()
        else:
            order_created_date = self.order_created_date

        delivery_date: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        elif isinstance(self.delivery_date, SearchComparator):
            delivery_date = self.delivery_date.to_dict()
        else:
            delivery_date = self.delivery_date

        picked_date: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.picked_date, Unset):
            picked_date = UNSET
        elif isinstance(self.picked_date, SearchComparator):
            picked_date = self.picked_date.to_dict()
        else:
            picked_date = self.picked_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if and_ is not UNSET:
            field_dict["and"] = and_
        if or_ is not UNSET:
            field_dict["or"] = or_
        if id is not UNSET:
            field_dict["id"] = id
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id
        if customer_ref is not UNSET:
            field_dict["customer_ref"] = customer_ref
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if status is not UNSET:
            field_dict["status"] = status
        if invoicing_status is not UNSET:
            field_dict["invoicing_status"] = invoicing_status
        if production_status is not UNSET:
            field_dict["production_status"] = production_status
        if source is not UNSET:
            field_dict["source"] = source
        if currency is not UNSET:
            field_dict["currency"] = currency
        if product_availability is not UNSET:
            field_dict["product_availability"] = product_availability
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ecommerce_order_type is not UNSET:
            field_dict["ecommerce_order_type"] = ecommerce_order_type
        if ecommerce_store_name is not UNSET:
            field_dict["ecommerce_store_name"] = ecommerce_store_name
        if ecommerce_order_id is not UNSET:
            field_dict["ecommerce_order_id"] = ecommerce_order_id
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if picked_date is not UNSET:
            field_dict["picked_date"] = picked_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_search_where_and_item import (
            SalesOrderSearchWhereAndItem,
        )
        from ..models.sales_order_search_where_or_item import (
            SalesOrderSearchWhereOrItem,
        )
        from ..models.search_comparator import SearchComparator

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[SalesOrderSearchWhereAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = SalesOrderSearchWhereAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[SalesOrderSearchWhereOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = SalesOrderSearchWhereOrItem.from_dict(
                    cast(Mapping[str, Any], or_item_data)
                )

                or_.append(or_item)

        def _parse_id(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_order_no(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        order_no = _parse_order_no(d.pop("order_no", UNSET))

        def _parse_customer_id(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        customer_id = _parse_customer_id(d.pop("customer_id", UNSET))

        def _parse_customer_ref(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))

        def _parse_location_id(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        location_id = _parse_location_id(d.pop("location_id", UNSET))

        def _parse_status(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_invoicing_status(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        invoicing_status = _parse_invoicing_status(d.pop("invoicing_status", UNSET))

        def _parse_production_status(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        production_status = _parse_production_status(d.pop("production_status", UNSET))

        def _parse_source(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        def _parse_currency(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_product_availability(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        product_availability = _parse_product_availability(
            d.pop("product_availability", UNSET)
        )

        def _parse_ingredient_availability(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        ingredient_availability = _parse_ingredient_availability(
            d.pop("ingredient_availability", UNSET)
        )

        def _parse_ecommerce_order_type(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        ecommerce_order_type = _parse_ecommerce_order_type(
            d.pop("ecommerce_order_type", UNSET)
        )

        def _parse_ecommerce_store_name(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        ecommerce_store_name = _parse_ecommerce_store_name(
            d.pop("ecommerce_store_name", UNSET)
        )

        def _parse_ecommerce_order_id(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        ecommerce_order_id = _parse_ecommerce_order_id(
            d.pop("ecommerce_order_id", UNSET)
        )

        def _parse_tracking_number(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_created_at(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_order_created_date(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        order_created_date = _parse_order_created_date(
            d.pop("order_created_date", UNSET)
        )

        def _parse_delivery_date(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

        def _parse_picked_date(
            data: object,
        ) -> bool | float | None | SearchComparator | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | None | SearchComparator | str | Unset, data)

        picked_date = _parse_picked_date(d.pop("picked_date", UNSET))

        sales_order_search_where = cls(
            and_=and_,
            or_=or_,
            id=id,
            order_no=order_no,
            customer_id=customer_id,
            customer_ref=customer_ref,
            location_id=location_id,
            status=status,
            invoicing_status=invoicing_status,
            production_status=production_status,
            source=source,
            currency=currency,
            product_availability=product_availability,
            ingredient_availability=ingredient_availability,
            ecommerce_order_type=ecommerce_order_type,
            ecommerce_store_name=ecommerce_store_name,
            ecommerce_order_id=ecommerce_order_id,
            tracking_number=tracking_number,
            created_at=created_at,
            updated_at=updated_at,
            order_created_date=order_created_date,
            delivery_date=delivery_date,
            picked_date=picked_date,
        )

        sales_order_search_where.additional_properties = d
        return sales_order_search_where

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
