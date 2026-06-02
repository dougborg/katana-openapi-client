from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_row_search_where_and_item import (
        SalesOrderRowSearchWhereAndItem,
    )
    from ..models.sales_order_row_search_where_or_item import (
        SalesOrderRowSearchWhereOrItem,
    )
    from ..models.search_comparator import SearchComparator


T = TypeVar("T", bound="SalesOrderRowSearchWhere")


@_attrs_define
class SalesOrderRowSearchWhere:
    """``where`` clause for ``POST /sales_order_rows/search``. Only the
    fields listed here may appear; unknown fields are rejected with
    422. Custom field values are addressable via additional
    ``custom_fields.<uuid>`` keys (snake_case), where ``<uuid>`` is the
    custom field definition id. Compose with ``and`` / ``or`` (max
    nesting depth 2).
    """

    and_: list[SalesOrderRowSearchWhereAndItem] | Unset = UNSET
    or_: list[SalesOrderRowSearchWhereOrItem] | Unset = UNSET
    id: bool | float | None | SearchComparator | str | Unset = UNSET
    sales_order_id: bool | float | None | SearchComparator | str | Unset = UNSET
    variant_id: bool | float | None | SearchComparator | str | Unset = UNSET
    location_id: bool | float | None | SearchComparator | str | Unset = UNSET
    tax_rate_id: bool | float | None | SearchComparator | str | Unset = UNSET
    quantity: bool | float | None | SearchComparator | str | Unset = UNSET
    price_per_unit: bool | float | None | SearchComparator | str | Unset = UNSET
    total_discount: bool | float | None | SearchComparator | str | Unset = UNSET
    tax_rate: bool | float | None | SearchComparator | str | Unset = UNSET
    currency: bool | float | None | SearchComparator | str | Unset = UNSET
    product_availability: bool | float | None | SearchComparator | str | Unset = UNSET
    created_at: bool | float | None | SearchComparator | str | Unset = UNSET
    updated_at: bool | float | None | SearchComparator | str | Unset = UNSET
    delivery_date: bool | float | None | SearchComparator | str | Unset = UNSET
    shipping_date: bool | float | None | SearchComparator | str | Unset = UNSET
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

        sales_order_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.sales_order_id, Unset):
            sales_order_id = UNSET
        elif isinstance(self.sales_order_id, SearchComparator):
            sales_order_id = self.sales_order_id.to_dict()
        else:
            sales_order_id = self.sales_order_id

        variant_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.variant_id, Unset):
            variant_id = UNSET
        elif isinstance(self.variant_id, SearchComparator):
            variant_id = self.variant_id.to_dict()
        else:
            variant_id = self.variant_id

        location_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.location_id, Unset):
            location_id = UNSET
        elif isinstance(self.location_id, SearchComparator):
            location_id = self.location_id.to_dict()
        else:
            location_id = self.location_id

        tax_rate_id: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.tax_rate_id, Unset):
            tax_rate_id = UNSET
        elif isinstance(self.tax_rate_id, SearchComparator):
            tax_rate_id = self.tax_rate_id.to_dict()
        else:
            tax_rate_id = self.tax_rate_id

        quantity: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.quantity, Unset):
            quantity = UNSET
        elif isinstance(self.quantity, SearchComparator):
            quantity = self.quantity.to_dict()
        else:
            quantity = self.quantity

        price_per_unit: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.price_per_unit, Unset):
            price_per_unit = UNSET
        elif isinstance(self.price_per_unit, SearchComparator):
            price_per_unit = self.price_per_unit.to_dict()
        else:
            price_per_unit = self.price_per_unit

        total_discount: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.total_discount, Unset):
            total_discount = UNSET
        elif isinstance(self.total_discount, SearchComparator):
            total_discount = self.total_discount.to_dict()
        else:
            total_discount = self.total_discount

        tax_rate: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.tax_rate, Unset):
            tax_rate = UNSET
        elif isinstance(self.tax_rate, SearchComparator):
            tax_rate = self.tax_rate.to_dict()
        else:
            tax_rate = self.tax_rate

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

        delivery_date: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        elif isinstance(self.delivery_date, SearchComparator):
            delivery_date = self.delivery_date.to_dict()
        else:
            delivery_date = self.delivery_date

        shipping_date: bool | dict[str, Any] | float | None | str | Unset
        if isinstance(self.shipping_date, Unset):
            shipping_date = UNSET
        elif isinstance(self.shipping_date, SearchComparator):
            shipping_date = self.shipping_date.to_dict()
        else:
            shipping_date = self.shipping_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if and_ is not UNSET:
            field_dict["and"] = and_
        if or_ is not UNSET:
            field_dict["or"] = or_
        if id is not UNSET:
            field_dict["id"] = id
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if total_discount is not UNSET:
            field_dict["total_discount"] = total_discount
        if tax_rate is not UNSET:
            field_dict["tax_rate"] = tax_rate
        if currency is not UNSET:
            field_dict["currency"] = currency
        if product_availability is not UNSET:
            field_dict["product_availability"] = product_availability
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if shipping_date is not UNSET:
            field_dict["shipping_date"] = shipping_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_row_search_where_and_item import (
            SalesOrderRowSearchWhereAndItem,
        )
        from ..models.sales_order_row_search_where_or_item import (
            SalesOrderRowSearchWhereOrItem,
        )
        from ..models.search_comparator import SearchComparator

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[SalesOrderRowSearchWhereAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = SalesOrderRowSearchWhereAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[SalesOrderRowSearchWhereOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = SalesOrderRowSearchWhereOrItem.from_dict(
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

        def _parse_sales_order_id(
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

        sales_order_id = _parse_sales_order_id(d.pop("sales_order_id", UNSET))

        def _parse_variant_id(
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

        variant_id = _parse_variant_id(d.pop("variant_id", UNSET))

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

        def _parse_tax_rate_id(
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

        tax_rate_id = _parse_tax_rate_id(d.pop("tax_rate_id", UNSET))

        def _parse_quantity(
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

        quantity = _parse_quantity(d.pop("quantity", UNSET))

        def _parse_price_per_unit(
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

        price_per_unit = _parse_price_per_unit(d.pop("price_per_unit", UNSET))

        def _parse_total_discount(
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

        total_discount = _parse_total_discount(d.pop("total_discount", UNSET))

        def _parse_tax_rate(
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

        tax_rate = _parse_tax_rate(d.pop("tax_rate", UNSET))

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

        def _parse_shipping_date(
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

        shipping_date = _parse_shipping_date(d.pop("shipping_date", UNSET))

        sales_order_row_search_where = cls(
            and_=and_,
            or_=or_,
            id=id,
            sales_order_id=sales_order_id,
            variant_id=variant_id,
            location_id=location_id,
            tax_rate_id=tax_rate_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_discount=total_discount,
            tax_rate=tax_rate,
            currency=currency,
            product_availability=product_availability,
            created_at=created_at,
            updated_at=updated_at,
            delivery_date=delivery_date,
            shipping_date=shipping_date,
        )

        sales_order_row_search_where.additional_properties = d
        return sales_order_row_search_where

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
