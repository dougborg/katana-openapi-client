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
    from ..models.manufacturing_order_recipe_row_batch_transactions_item import (
        ManufacturingOrderRecipeRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="ManufacturingOrderRecipeRow")


@_attrs_define
class ManufacturingOrderRecipeRow:
    """Represents an ingredient or component required for a manufacturing order, tracking planned and actual quantities
    used in production.

        Example:
            {'id': 4001, 'manufacturing_order_id': 3001, 'variant_id': 3201, 'notes': 'Use only grade 304 material',
                'planned_quantity_per_unit': 2.5, 'total_actual_quantity': 125.0, 'ingredient_availability': 'IN_STOCK',
                'batch_transactions': [{'batch_id': 1201, 'quantity': 125.0}], 'cost': 437.5, 'created_at':
                '2024-01-15T08:00:00Z', 'updated_at': '2024-01-20T14:30:00Z', 'deleted_at': None}
    """

    id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    manufacturing_order_id: int | Unset = UNSET
    variant_id: int | Unset = UNSET
    notes: str | Unset = UNSET
    planned_quantity_per_unit: float | Unset = UNSET
    total_actual_quantity: float | Unset = UNSET
    ingredient_availability: str | Unset = UNSET
    ingredient_expected_date: datetime.datetime | None | Unset = UNSET
    batch_transactions: (
        list[ManufacturingOrderRecipeRowBatchTransactionsItem] | Unset
    ) = UNSET
    cost: float | Unset = UNSET
    total_consumed_quantity: float | Unset = UNSET
    total_remaining_quantity: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        manufacturing_order_id = self.manufacturing_order_id

        variant_id = self.variant_id

        notes = self.notes

        planned_quantity_per_unit = self.planned_quantity_per_unit

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

        total_consumed_quantity = self.total_consumed_quantity

        total_remaining_quantity = self.total_remaining_quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if manufacturing_order_id is not UNSET:
            field_dict["manufacturing_order_id"] = manufacturing_order_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if planned_quantity_per_unit is not UNSET:
            field_dict["planned_quantity_per_unit"] = planned_quantity_per_unit
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
        if total_consumed_quantity is not UNSET:
            field_dict["total_consumed_quantity"] = total_consumed_quantity
        if total_remaining_quantity is not UNSET:
            field_dict["total_remaining_quantity"] = total_remaining_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manufacturing_order_recipe_row_batch_transactions_item import (
            ManufacturingOrderRecipeRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        manufacturing_order_id = d.pop("manufacturing_order_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        notes = d.pop("notes", UNSET)

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit", UNSET)

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
            list[ManufacturingOrderRecipeRowBatchTransactionsItem] | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = (
                    ManufacturingOrderRecipeRowBatchTransactionsItem.from_dict(
                        batch_transactions_item_data
                    )
                )

                batch_transactions.append(batch_transactions_item)

        cost = d.pop("cost", UNSET)

        total_consumed_quantity = d.pop("total_consumed_quantity", UNSET)

        total_remaining_quantity = d.pop("total_remaining_quantity", UNSET)

        manufacturing_order_recipe_row = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            manufacturing_order_id=manufacturing_order_id,
            variant_id=variant_id,
            notes=notes,
            planned_quantity_per_unit=planned_quantity_per_unit,
            total_actual_quantity=total_actual_quantity,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            batch_transactions=batch_transactions,
            cost=cost,
            total_consumed_quantity=total_consumed_quantity,
            total_remaining_quantity=total_remaining_quantity,
        )

        manufacturing_order_recipe_row.additional_properties = d
        return manufacturing_order_recipe_row

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
