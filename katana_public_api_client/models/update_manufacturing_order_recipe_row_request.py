from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_manufacturing_order_recipe_row_request_batch_transactions_item import (
        UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
    )


T = TypeVar("T", bound="UpdateManufacturingOrderRecipeRowRequest")


@_attrs_define
class UpdateManufacturingOrderRecipeRowRequest:
    """Request payload for updating a manufacturing order recipe row with actual consumption data and revised requirements

    Example:
        {'variant_id': 2002, 'notes': 'Used organic ingredients as requested by customer', 'planned_quantity_per_unit':
            0.3, 'total_actual_quantity': 6.2, 'batch_transactions': [{'batch_id': 301, 'quantity': 3.5}, {'batch_id': 302,
            'quantity': 2.7}]}
    """

    variant_id: int | Unset = UNSET
    notes: str | Unset = UNSET
    planned_quantity_per_unit: float | Unset = UNSET
    total_actual_quantity: float | Unset = UNSET
    batch_transactions: (
        list[UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        notes = self.notes

        planned_quantity_per_unit = self.planned_quantity_per_unit

        total_actual_quantity = self.total_actual_quantity

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if planned_quantity_per_unit is not UNSET:
            field_dict["planned_quantity_per_unit"] = planned_quantity_per_unit
        if total_actual_quantity is not UNSET:
            field_dict["total_actual_quantity"] = total_actual_quantity
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_manufacturing_order_recipe_row_request_batch_transactions_item import (
            UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        notes = d.pop("notes", UNSET)

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit", UNSET)

        total_actual_quantity = d.pop("total_actual_quantity", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: (
            list[UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        update_manufacturing_order_recipe_row_request = cls(
            variant_id=variant_id,
            notes=notes,
            planned_quantity_per_unit=planned_quantity_per_unit,
            total_actual_quantity=total_actual_quantity,
            batch_transactions=batch_transactions,
        )

        update_manufacturing_order_recipe_row_request.additional_properties = d
        return update_manufacturing_order_recipe_row_request

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
