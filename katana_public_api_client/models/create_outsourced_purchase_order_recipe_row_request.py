from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_transaction_request import BatchTransactionRequest


T = TypeVar("T", bound="CreateOutsourcedPurchaseOrderRecipeRowRequest")


@_attrs_define
class CreateOutsourcedPurchaseOrderRecipeRowRequest:
    """Request payload for creating a new outsourced purchase order recipe row"""

    purchase_order_row_id: int
    ingredient_variant_id: int
    planned_quantity_per_unit: float
    notes: str | Unset = UNSET
    batch_transactions: list[BatchTransactionRequest] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        purchase_order_row_id = self.purchase_order_row_id

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

        field_dict.update(
            {
                "purchase_order_row_id": purchase_order_row_id,
                "ingredient_variant_id": ingredient_variant_id,
                "planned_quantity_per_unit": planned_quantity_per_unit,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction_request import BatchTransactionRequest

        d = dict(src_dict)
        purchase_order_row_id = d.pop("purchase_order_row_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

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

        create_outsourced_purchase_order_recipe_row_request = cls(
            purchase_order_row_id=purchase_order_row_id,
            ingredient_variant_id=ingredient_variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            batch_transactions=batch_transactions,
        )

        return create_outsourced_purchase_order_recipe_row_request
