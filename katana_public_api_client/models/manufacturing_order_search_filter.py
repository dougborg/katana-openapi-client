from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_search_filter_and_item import (
        ManufacturingOrderSearchFilterAndItem,
    )
    from ..models.manufacturing_order_search_filter_or_item import (
        ManufacturingOrderSearchFilterOrItem,
    )
    from ..models.search_comparator import SearchComparator


T = TypeVar("T", bound="ManufacturingOrderSearchFilter")


@_attrs_define
class ManufacturingOrderSearchFilter:
    """Filter clause for ``POST /manufacturing_orders/search``. Only the fields listed
    here may appear; unknown fields are rejected with 422. Custom field
    values are addressable via ``custom_fields.<uuid>`` keys.
    """

    and_: list[ManufacturingOrderSearchFilterAndItem] | Unset = UNSET
    or_: list[ManufacturingOrderSearchFilterOrItem] | Unset = UNSET
    actual_quantity: bool | float | SearchComparator | str | Unset | None = UNSET
    completed_quantity: bool | float | SearchComparator | str | Unset | None = UNSET
    created_at: bool | float | SearchComparator | str | Unset | None = UNSET
    done_date: bool | float | SearchComparator | str | Unset | None = UNSET
    id: bool | float | SearchComparator | str | Unset | None = UNSET
    includes_partial_completions: (
        bool | float | SearchComparator | str | Unset | None
    ) = UNSET
    ingredient_availability: bool | float | SearchComparator | str | Unset | None = (
        UNSET
    )
    is_linked_to_sales_order: bool | float | SearchComparator | str | Unset | None = (
        UNSET
    )
    location_id: bool | float | SearchComparator | str | Unset | None = UNSET
    order_created_date: bool | float | SearchComparator | str | Unset | None = UNSET
    order_no: bool | float | SearchComparator | str | Unset | None = UNSET
    planned_quantity: bool | float | SearchComparator | str | Unset | None = UNSET
    production_deadline_date: bool | float | SearchComparator | str | Unset | None = (
        UNSET
    )
    remaining_quantity: bool | float | SearchComparator | str | Unset | None = UNSET
    status: bool | float | SearchComparator | str | Unset | None = UNSET
    total_cost: bool | float | SearchComparator | str | Unset | None = UNSET
    updated_at: bool | float | SearchComparator | str | Unset | None = UNSET
    variant_id: bool | float | SearchComparator | str | Unset | None = UNSET
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

        actual_quantity: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.actual_quantity, Unset):
            actual_quantity = UNSET
        elif isinstance(self.actual_quantity, SearchComparator):
            actual_quantity = self.actual_quantity.to_dict()
        else:
            actual_quantity = self.actual_quantity

        completed_quantity: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.completed_quantity, Unset):
            completed_quantity = UNSET
        elif isinstance(self.completed_quantity, SearchComparator):
            completed_quantity = self.completed_quantity.to_dict()
        else:
            completed_quantity = self.completed_quantity

        created_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, SearchComparator):
            created_at = self.created_at.to_dict()
        else:
            created_at = self.created_at

        done_date: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.done_date, Unset):
            done_date = UNSET
        elif isinstance(self.done_date, SearchComparator):
            done_date = self.done_date.to_dict()
        else:
            done_date = self.done_date

        id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, SearchComparator):
            id = self.id.to_dict()
        else:
            id = self.id

        includes_partial_completions: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.includes_partial_completions, Unset):
            includes_partial_completions = UNSET
        elif isinstance(self.includes_partial_completions, SearchComparator):
            includes_partial_completions = self.includes_partial_completions.to_dict()
        else:
            includes_partial_completions = self.includes_partial_completions

        ingredient_availability: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.ingredient_availability, Unset):
            ingredient_availability = UNSET
        elif isinstance(self.ingredient_availability, SearchComparator):
            ingredient_availability = self.ingredient_availability.to_dict()
        else:
            ingredient_availability = self.ingredient_availability

        is_linked_to_sales_order: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.is_linked_to_sales_order, Unset):
            is_linked_to_sales_order = UNSET
        elif isinstance(self.is_linked_to_sales_order, SearchComparator):
            is_linked_to_sales_order = self.is_linked_to_sales_order.to_dict()
        else:
            is_linked_to_sales_order = self.is_linked_to_sales_order

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

        planned_quantity: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.planned_quantity, Unset):
            planned_quantity = UNSET
        elif isinstance(self.planned_quantity, SearchComparator):
            planned_quantity = self.planned_quantity.to_dict()
        else:
            planned_quantity = self.planned_quantity

        production_deadline_date: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.production_deadline_date, Unset):
            production_deadline_date = UNSET
        elif isinstance(self.production_deadline_date, SearchComparator):
            production_deadline_date = self.production_deadline_date.to_dict()
        else:
            production_deadline_date = self.production_deadline_date

        remaining_quantity: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.remaining_quantity, Unset):
            remaining_quantity = UNSET
        elif isinstance(self.remaining_quantity, SearchComparator):
            remaining_quantity = self.remaining_quantity.to_dict()
        else:
            remaining_quantity = self.remaining_quantity

        status: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, SearchComparator):
            status = self.status.to_dict()
        else:
            status = self.status

        total_cost: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.total_cost, Unset):
            total_cost = UNSET
        elif isinstance(self.total_cost, SearchComparator):
            total_cost = self.total_cost.to_dict()
        else:
            total_cost = self.total_cost

        updated_at: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, SearchComparator):
            updated_at = self.updated_at.to_dict()
        else:
            updated_at = self.updated_at

        variant_id: bool | dict[str, Any] | float | str | Unset | None
        if isinstance(self.variant_id, Unset):
            variant_id = UNSET
        elif isinstance(self.variant_id, SearchComparator):
            variant_id = self.variant_id.to_dict()
        else:
            variant_id = self.variant_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if and_ is not UNSET:
            field_dict["and"] = and_
        if or_ is not UNSET:
            field_dict["or"] = or_
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if completed_quantity is not UNSET:
            field_dict["completed_quantity"] = completed_quantity
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if done_date is not UNSET:
            field_dict["done_date"] = done_date
        if id is not UNSET:
            field_dict["id"] = id
        if includes_partial_completions is not UNSET:
            field_dict["includes_partial_completions"] = includes_partial_completions
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if is_linked_to_sales_order is not UNSET:
            field_dict["is_linked_to_sales_order"] = is_linked_to_sales_order
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if planned_quantity is not UNSET:
            field_dict["planned_quantity"] = planned_quantity
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date
        if remaining_quantity is not UNSET:
            field_dict["remaining_quantity"] = remaining_quantity
        if status is not UNSET:
            field_dict["status"] = status
        if total_cost is not UNSET:
            field_dict["total_cost"] = total_cost
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manufacturing_order_search_filter_and_item import (
            ManufacturingOrderSearchFilterAndItem,
        )
        from ..models.manufacturing_order_search_filter_or_item import (
            ManufacturingOrderSearchFilterOrItem,
        )
        from ..models.search_comparator import SearchComparator

        d = dict(src_dict)
        _and_ = d.pop("and", UNSET)
        and_: list[ManufacturingOrderSearchFilterAndItem] | Unset = UNSET
        if _and_ is not UNSET:
            and_ = []
            for and_item_data in _and_:
                and_item = ManufacturingOrderSearchFilterAndItem.from_dict(
                    cast(Mapping[str, Any], and_item_data)
                )

                and_.append(and_item)

        _or_ = d.pop("or", UNSET)
        or_: list[ManufacturingOrderSearchFilterOrItem] | Unset = UNSET
        if _or_ is not UNSET:
            or_ = []
            for or_item_data in _or_:
                or_item = ManufacturingOrderSearchFilterOrItem.from_dict(
                    cast(Mapping[str, Any], or_item_data)
                )

                or_.append(or_item)

        def _parse_actual_quantity(
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

        actual_quantity = _parse_actual_quantity(d.pop("actual_quantity", UNSET))

        def _parse_completed_quantity(
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

        completed_quantity = _parse_completed_quantity(
            d.pop("completed_quantity", UNSET)
        )

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

        def _parse_done_date(
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

        done_date = _parse_done_date(d.pop("done_date", UNSET))

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

        def _parse_includes_partial_completions(
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

        includes_partial_completions = _parse_includes_partial_completions(
            d.pop("includes_partial_completions", UNSET)
        )

        def _parse_ingredient_availability(
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

        ingredient_availability = _parse_ingredient_availability(
            d.pop("ingredient_availability", UNSET)
        )

        def _parse_is_linked_to_sales_order(
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

        is_linked_to_sales_order = _parse_is_linked_to_sales_order(
            d.pop("is_linked_to_sales_order", UNSET)
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

        def _parse_planned_quantity(
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

        planned_quantity = _parse_planned_quantity(d.pop("planned_quantity", UNSET))

        def _parse_production_deadline_date(
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

        production_deadline_date = _parse_production_deadline_date(
            d.pop("production_deadline_date", UNSET)
        )

        def _parse_remaining_quantity(
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

        remaining_quantity = _parse_remaining_quantity(
            d.pop("remaining_quantity", UNSET)
        )

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

        def _parse_total_cost(
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

        total_cost = _parse_total_cost(d.pop("total_cost", UNSET))

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

        def _parse_variant_id(
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

        variant_id = _parse_variant_id(d.pop("variant_id", UNSET))

        manufacturing_order_search_filter = cls(
            and_=and_,
            or_=or_,
            actual_quantity=actual_quantity,
            completed_quantity=completed_quantity,
            created_at=created_at,
            done_date=done_date,
            id=id,
            includes_partial_completions=includes_partial_completions,
            ingredient_availability=ingredient_availability,
            is_linked_to_sales_order=is_linked_to_sales_order,
            location_id=location_id,
            order_created_date=order_created_date,
            order_no=order_no,
            planned_quantity=planned_quantity,
            production_deadline_date=production_deadline_date,
            remaining_quantity=remaining_quantity,
            status=status,
            total_cost=total_cost,
            updated_at=updated_at,
            variant_id=variant_id,
        )

        manufacturing_order_search_filter.additional_properties = d
        return manufacturing_order_search_filter

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
