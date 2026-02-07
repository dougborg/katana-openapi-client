from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_transaction_request import BatchTransactionRequest


T = TypeVar("T", bound="UpdateOutsourcedPurchaseOrderRecipeRowRequest")


@_attrs_define
class UpdateOutsourcedPurchaseOrderRecipeRowRequest:
    """Request payload for updating an outsourced purchase order recipe row"""

    ingredient_variant_id: int | Unset = UNSET
    planned_quantity_per_unit: float | Unset = UNSET
    notes: str | Unset = UNSET
    batch_transactions: list[BatchTransactionRequest] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        ingredient_variant_id = self.ingredient_variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

        notes = self.notes

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if ingredient_variant_id is not UNSET:
            field_dict["ingredient_variant_id"] = ingredient_variant_id
        if planned_quantity_per_unit is not UNSET:
            field_dict["planned_quantity_per_unit"] = planned_quantity_per_unit
        if notes is not UNSET:
            field_dict["notes"] = notes
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction_request import BatchTransactionRequest

        d = dict(src_dict)
        ingredient_variant_id = d.pop("ingredient_variant_id", UNSET)

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit", UNSET)

        notes = d.pop("notes", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransactionRequest] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransactionRequest.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        update_outsourced_purchase_order_recipe_row_request = cls(
            ingredient_variant_id=ingredient_variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            batch_transactions=batch_transactions,
        )

        return update_outsourced_purchase_order_recipe_row_request
