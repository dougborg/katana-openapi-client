from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_comparator import SearchComparator
    from ..models.variant_search_filter_and_item import VariantSearchFilterAndItem
    from ..models.variant_search_filter_or_item import VariantSearchFilterOrItem


T = TypeVar("T", bound="VariantSearchFilter")


@_attrs_define
class VariantSearchFilter:
    """Filter clause for ``POST /variants/search``. Only the fields listed
    here may appear; unknown fields are rejected with 422. Custom field
    values are addressable via ``custom_fields.<uuid>`` keys.
    """

    and_: list[VariantSearchFilterAndItem] | Unset = UNSET
    or_: list[VariantSearchFilterOrItem] | Unset = UNSET
    abc_classification: bool | float | SearchComparator | str | Unset | None = UNSET
    created_at: bool | float | SearchComparator | str | Unset | None = UNSET
    id: bool | float | SearchComparator | str | Unset | None = UNSET
    internal_barcode: bool | float | SearchComparator | str | Unset | None = UNSET
    item_id: bool | float | SearchComparator | str | Unset | None = UNSET
    item_type: bool | float | SearchComparator | str | Unset | None = UNSET
    lead_time: bool | float | SearchComparator | str | Unset | None = UNSET
    minimum_order_quantity: bool | float | SearchComparator | str | Unset | None = UNSET
    purchase_price: bool | float | SearchComparator | str | Unset | None = UNSET
    registered_barcode: bool | float | SearchComparator | str | Unset | None = UNSET
    sales_price: bool | float | SearchComparator | str | Unset | None = UNSET
    sku: bool | float | SearchComparator | str | Unset | None = UNSET
    supplier_item_codes: bool | float | SearchComparator | str | Unset | None = UNSET
    updated_at: bool | float | SearchComparator | str | Unset | None = UNSET
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

        abc_classification: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.abc_classification, Unset):
            abc_classification = UNSET
        elif isinstance(self.abc_classification, SearchComparator):
            abc_classification = self.abc_classification.to_dict()
        else:
            abc_classification = self.abc_classification

        created_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, SearchComparator):
            created_at = self.created_at.to_dict()
        else:
            created_at = self.created_at

        id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, SearchComparator):
            id = self.id.to_dict()
        else:
            id = self.id

        internal_barcode: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.internal_barcode, Unset):
            internal_barcode = UNSET
        elif isinstance(self.internal_barcode, SearchComparator):
            internal_barcode = self.internal_barcode.to_dict()
        else:
            internal_barcode = self.internal_barcode

        item_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.item_id, Unset):
            item_id = UNSET
        elif isinstance(self.item_id, SearchComparator):
            item_id = self.item_id.to_dict()
        else:
            item_id = self.item_id

        item_type: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.item_type, Unset):
            item_type = UNSET
        elif isinstance(self.item_type, SearchComparator):
            item_type = self.item_type.to_dict()
        else:
            item_type = self.item_type

        lead_time: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.lead_time, Unset):
            lead_time = UNSET
        elif isinstance(self.lead_time, SearchComparator):
            lead_time = self.lead_time.to_dict()
        else:
            lead_time = self.lead_time

        minimum_order_quantity: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.minimum_order_quantity, Unset):
            minimum_order_quantity = UNSET
        elif isinstance(self.minimum_order_quantity, SearchComparator):
            minimum_order_quantity = self.minimum_order_quantity.to_dict()
        else:
            minimum_order_quantity = self.minimum_order_quantity

        purchase_price: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.purchase_price, Unset):
            purchase_price = UNSET
        elif isinstance(self.purchase_price, SearchComparator):
            purchase_price = self.purchase_price.to_dict()
        else:
            purchase_price = self.purchase_price

        registered_barcode: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.registered_barcode, Unset):
            registered_barcode = UNSET
        elif isinstance(self.registered_barcode, SearchComparator):
            registered_barcode = self.registered_barcode.to_dict()
        else:
            registered_barcode = self.registered_barcode

        sales_price: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        elif isinstance(self.sales_price, SearchComparator):
            sales_price = self.sales_price.to_dict()
        else:
            sales_price = self.sales_price

        sku: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.sku, Unset):
            sku = UNSET
        elif isinstance(self.sku, SearchComparator):
            sku = self.sku.to_dict()
        else:
            sku = self.sku

        supplier_item_codes: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.supplier_item_codes, Unset):
            supplier_item_codes = UNSET
        elif isinstance(self.supplier_item_codes, SearchComparator):
            supplier_item_codes = self.supplier_item_codes.to_dict()
        else:
            supplier_item_codes = self.supplier_item_codes

        updated_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, SearchComparator):
            updated_at = self.updated_at.to_dict()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if and_ is not UNSET:
            field_dict["and"] = and_
        if or_ is not UNSET:
            field_dict["or"] = or_
        if abc_classification is not UNSET:
            field_dict["abc_classification"] = abc_classification
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if id is not UNSET:
            field_dict["id"] = id
        if internal_barcode is not UNSET:
            field_dict["internal_barcode"] = internal_barcode
        if item_id is not UNSET:
            field_dict["item_id"] = item_id
        if item_type is not UNSET:
            field_dict["item_type"] = item_type
        if lead_time is not UNSET:
            field_dict["lead_time"] = lead_time
        if minimum_order_quantity is not UNSET:
            field_dict["minimum_order_quantity"] = minimum_order_quantity
        if purchase_price is not UNSET:
            field_dict["purchase_price"] = purchase_price
        if registered_barcode is not UNSET:
            field_dict["registered_barcode"] = registered_barcode
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if sku is not UNSET:
            field_dict["sku"] = sku
        if supplier_item_codes is not UNSET:
            field_dict["supplier_item_codes"] = supplier_item_codes
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_comparator import SearchComparator
        from ..models.variant_search_filter_and_item import (
            VariantSearchFilterAndItem,
        )
        from ..models.variant_search_filter_or_item import (
            VariantSearchFilterOrItem,
        )

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[VariantSearchFilterAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = VariantSearchFilterAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[VariantSearchFilterOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = VariantSearchFilterOrItem.from_dict(
                    cast(Mapping[str, Any], or_item_data)
                )

                or_.append(or_item)

        def _parse_abc_classification(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        abc_classification = _parse_abc_classification(
            d.pop("abc_classification", UNSET)
        )

        def _parse_created_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_internal_barcode(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        internal_barcode = _parse_internal_barcode(d.pop("internal_barcode", UNSET))

        def _parse_item_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        item_id = _parse_item_id(d.pop("item_id", UNSET))

        def _parse_item_type(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        item_type = _parse_item_type(d.pop("item_type", UNSET))

        def _parse_lead_time(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        lead_time = _parse_lead_time(d.pop("lead_time", UNSET))

        def _parse_minimum_order_quantity(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        minimum_order_quantity = _parse_minimum_order_quantity(
            d.pop("minimum_order_quantity", UNSET)
        )

        def _parse_purchase_price(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        purchase_price = _parse_purchase_price(d.pop("purchase_price", UNSET))

        def _parse_registered_barcode(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        registered_barcode = _parse_registered_barcode(
            d.pop("registered_barcode", UNSET)
        )

        def _parse_sales_price(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_sku(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        sku = _parse_sku(d.pop("sku", UNSET))

        def _parse_supplier_item_codes(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        supplier_item_codes = _parse_supplier_item_codes(
            d.pop("supplier_item_codes", UNSET)
        )

        def _parse_updated_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_search_predicate_type_1 = SearchComparator.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return componentsschemas_search_predicate_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        variant_search_filter = cls(
            and_=and_,
            or_=or_,
            abc_classification=abc_classification,
            created_at=created_at,
            id=id,
            internal_barcode=internal_barcode,
            item_id=item_id,
            item_type=item_type,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            purchase_price=purchase_price,
            registered_barcode=registered_barcode,
            sales_price=sales_price,
            sku=sku,
            supplier_item_codes=supplier_item_codes,
            updated_at=updated_at,
        )

        variant_search_filter.additional_properties = d
        return variant_search_filter

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
