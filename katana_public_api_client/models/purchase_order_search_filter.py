from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_search_filter_and_item import (
        PurchaseOrderSearchFilterAndItem,
    )
    from ..models.purchase_order_search_filter_or_item import (
        PurchaseOrderSearchFilterOrItem,
    )
    from ..models.search_comparator import SearchComparator


T = TypeVar("T", bound="PurchaseOrderSearchFilter")


@_attrs_define
class PurchaseOrderSearchFilter:
    """Filter clause for ``POST /purchase_orders/search``. Only the fields listed
    here may appear; unknown fields are rejected with 422. Custom field
    values are addressable via ``custom_fields.<uuid>`` keys.
    """

    and_: list[PurchaseOrderSearchFilterAndItem] | Unset = UNSET
    or_: list[PurchaseOrderSearchFilterOrItem] | Unset = UNSET
    billing_status: bool | float | SearchComparator | str | Unset | None = UNSET
    created_at: bool | float | SearchComparator | str | Unset | None = UNSET
    currency: bool | float | SearchComparator | str | Unset | None = UNSET
    default_group_id: bool | float | SearchComparator | str | Unset | None = UNSET
    entity_type: bool | float | SearchComparator | str | Unset | None = UNSET
    expected_arrival_date: bool | float | SearchComparator | str | Unset | None = UNSET
    id: bool | float | SearchComparator | str | Unset | None = UNSET
    last_document_status: bool | float | SearchComparator | str | Unset | None = UNSET
    location_id: bool | float | SearchComparator | str | Unset | None = UNSET
    order_created_date: bool | float | SearchComparator | str | Unset | None = UNSET
    order_no: bool | float | SearchComparator | str | Unset | None = UNSET
    status: bool | float | SearchComparator | str | Unset | None = UNSET
    supplier_id: bool | float | SearchComparator | str | Unset | None = UNSET
    tracking_location_id: bool | float | SearchComparator | str | Unset | None = UNSET
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

        billing_status: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.billing_status, Unset):
            billing_status = UNSET
        elif isinstance(self.billing_status, SearchComparator):
            billing_status = self.billing_status.to_dict()
        else:
            billing_status = self.billing_status

        created_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, SearchComparator):
            created_at = self.created_at.to_dict()
        else:
            created_at = self.created_at

        currency: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.currency, Unset):
            currency = UNSET
        elif isinstance(self.currency, SearchComparator):
            currency = self.currency.to_dict()
        else:
            currency = self.currency

        default_group_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.default_group_id, Unset):
            default_group_id = UNSET
        elif isinstance(self.default_group_id, SearchComparator):
            default_group_id = self.default_group_id.to_dict()
        else:
            default_group_id = self.default_group_id

        entity_type: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.entity_type, Unset):
            entity_type = UNSET
        elif isinstance(self.entity_type, SearchComparator):
            entity_type = self.entity_type.to_dict()
        else:
            entity_type = self.entity_type

        expected_arrival_date: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = UNSET
        elif isinstance(self.expected_arrival_date, SearchComparator):
            expected_arrival_date = self.expected_arrival_date.to_dict()
        else:
            expected_arrival_date = self.expected_arrival_date

        id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, SearchComparator):
            id = self.id.to_dict()
        else:
            id = self.id

        last_document_status: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.last_document_status, Unset):
            last_document_status = UNSET
        elif isinstance(self.last_document_status, SearchComparator):
            last_document_status = self.last_document_status.to_dict()
        else:
            last_document_status = self.last_document_status

        location_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.location_id, Unset):
            location_id = UNSET
        elif isinstance(self.location_id, SearchComparator):
            location_id = self.location_id.to_dict()
        else:
            location_id = self.location_id

        order_created_date: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.order_created_date, Unset):
            order_created_date = UNSET
        elif isinstance(self.order_created_date, SearchComparator):
            order_created_date = self.order_created_date.to_dict()
        else:
            order_created_date = self.order_created_date

        order_no: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.order_no, Unset):
            order_no = UNSET
        elif isinstance(self.order_no, SearchComparator):
            order_no = self.order_no.to_dict()
        else:
            order_no = self.order_no

        status: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, SearchComparator):
            status = self.status.to_dict()
        else:
            status = self.status

        supplier_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.supplier_id, Unset):
            supplier_id = UNSET
        elif isinstance(self.supplier_id, SearchComparator):
            supplier_id = self.supplier_id.to_dict()
        else:
            supplier_id = self.supplier_id

        tracking_location_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.tracking_location_id, Unset):
            tracking_location_id = UNSET
        elif isinstance(self.tracking_location_id, SearchComparator):
            tracking_location_id = self.tracking_location_id.to_dict()
        else:
            tracking_location_id = self.tracking_location_id

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
        if billing_status is not UNSET:
            field_dict["billing_status"] = billing_status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if currency is not UNSET:
            field_dict["currency"] = currency
        if default_group_id is not UNSET:
            field_dict["default_group_id"] = default_group_id
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if id is not UNSET:
            field_dict["id"] = id
        if last_document_status is not UNSET:
            field_dict["last_document_status"] = last_document_status
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if status is not UNSET:
            field_dict["status"] = status
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
        if tracking_location_id is not UNSET:
            field_dict["tracking_location_id"] = tracking_location_id
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_search_filter_and_item import (
            PurchaseOrderSearchFilterAndItem,
        )
        from ..models.purchase_order_search_filter_or_item import (
            PurchaseOrderSearchFilterOrItem,
        )
        from ..models.search_comparator import SearchComparator

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[PurchaseOrderSearchFilterAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = PurchaseOrderSearchFilterAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[PurchaseOrderSearchFilterOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = PurchaseOrderSearchFilterOrItem.from_dict(
                    cast(Mapping[str, Any], or_item_data)
                )

                or_.append(or_item)

        def _parse_billing_status(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        billing_status = _parse_billing_status(d.pop("billing_status", UNSET))

        def _parse_created_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_currency(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_default_group_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        default_group_id = _parse_default_group_id(d.pop("default_group_id", UNSET))

        def _parse_entity_type(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        entity_type = _parse_entity_type(d.pop("entity_type", UNSET))

        def _parse_expected_arrival_date(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        expected_arrival_date = _parse_expected_arrival_date(
            d.pop("expected_arrival_date", UNSET)
        )

        def _parse_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_last_document_status(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        last_document_status = _parse_last_document_status(
            d.pop("last_document_status", UNSET)
        )

        def _parse_location_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        location_id = _parse_location_id(d.pop("location_id", UNSET))

        def _parse_order_created_date(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        order_created_date = _parse_order_created_date(
            d.pop("order_created_date", UNSET)
        )

        def _parse_order_no(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        order_no = _parse_order_no(d.pop("order_no", UNSET))

        def _parse_status(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_supplier_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        supplier_id = _parse_supplier_id(d.pop("supplier_id", UNSET))

        def _parse_tracking_location_id(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        tracking_location_id = _parse_tracking_location_id(
            d.pop("tracking_location_id", UNSET)
        )

        def _parse_updated_at(
            data: object,
        ) -> bool | float | SearchComparator | str | Unset | None:
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
            return cast(bool | float | SearchComparator | str | Unset | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        purchase_order_search_filter = cls(
            and_=and_,
            or_=or_,
            billing_status=billing_status,
            created_at=created_at,
            currency=currency,
            default_group_id=default_group_id,
            entity_type=entity_type,
            expected_arrival_date=expected_arrival_date,
            id=id,
            last_document_status=last_document_status,
            location_id=location_id,
            order_created_date=order_created_date,
            order_no=order_no,
            status=status,
            supplier_id=supplier_id,
            tracking_location_id=tracking_location_id,
            updated_at=updated_at,
        )

        purchase_order_search_filter.additional_properties = d
        return purchase_order_search_filter

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
