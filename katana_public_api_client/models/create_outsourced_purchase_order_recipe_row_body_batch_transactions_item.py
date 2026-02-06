from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar(
    "T", bound="CreateOutsourcedPurchaseOrderRecipeRowBodyBatchTransactionsItem"
)


@_attrs_define
class CreateOutsourcedPurchaseOrderRecipeRowBodyBatchTransactionsItem:
    batch_id: int | Unset = UNSET
    quantity: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        create_outsourced_purchase_order_recipe_row_body_batch_transactions_item = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        return create_outsourced_purchase_order_recipe_row_body_batch_transactions_item
