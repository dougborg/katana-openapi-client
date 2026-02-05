from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
        CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
    )


T = TypeVar("T", bound="CreateManufacturingOrderRecipeRowRequest")


@_attrs_define
class CreateManufacturingOrderRecipeRowRequest:
    """Request payload for creating a new manufacturing order recipe row to track ingredient requirements and consumption

    Example:
        {'manufacturing_order_id': 1001, 'variant_id': 2002, 'notes': 'Use fresh ingredients from cold storage',
            'planned_quantity_per_unit': 0.25, 'total_actual_quantity': 5.0, 'ingredient_availability': 'AVAILABLE',
            'ingredient_expected_date': '2023-10-15T08:00:00Z', 'batch_transactions': [{'batch_id': 301, 'quantity': 3.0},
            {'batch_id': 302, 'quantity': 2.0}], 'cost': 12.5}
    """

    manufacturing_order_id: int
    variant_id: int
    planned_quantity_per_unit: float
    notes: str | Unset = UNSET
    total_actual_quantity: float | Unset = UNSET
    ingredient_availability: str | Unset = UNSET
    ingredient_expected_date: datetime.datetime | None | Unset = UNSET
    batch_transactions: (
        list[CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
    ) = UNSET
    cost: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        variant_id = self.variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

        notes = self.notes

        total_actual_quantity = self.total_actual_quantity

        ingredient_availability = self.ingredient_availability

        ingredient_expected_date: None | str | Unset
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        elif isinstance(self.ingredient_expected_date, datetime.datetime):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()
        else:
            ingredient_expected_date = self.ingredient_expected_date

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        cost = self.cost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "variant_id": variant_id,
                "planned_quantity_per_unit": planned_quantity_per_unit,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if total_actual_quantity is not UNSET:
            field_dict["total_actual_quantity"] = total_actual_quantity
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if cost is not UNSET:
            field_dict["cost"] = cost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
            CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
        )

        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        variant_id = d.pop("variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

        notes = d.pop("notes", UNSET)

        total_actual_quantity = d.pop("total_actual_quantity", UNSET)

        ingredient_availability = d.pop("ingredient_availability", UNSET)

        def _parse_ingredient_expected_date(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_expected_date_type_0 = isoparse(data)

                return ingredient_expected_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ingredient_expected_date = _parse_ingredient_expected_date(
            d.pop("ingredient_expected_date", UNSET)
        )

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: (
            list[CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        cost = d.pop("cost", UNSET)

        create_manufacturing_order_recipe_row_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            variant_id=variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            total_actual_quantity=total_actual_quantity,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            batch_transactions=batch_transactions,
            cost=cost,
        )

        create_manufacturing_order_recipe_row_request.additional_properties = d
        return create_manufacturing_order_recipe_row_request

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
