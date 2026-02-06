from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_transaction import BatchTransaction


T = TypeVar("T", bound="UpdateManufacturingOrderProductionIngredientRequest")


@_attrs_define
class UpdateManufacturingOrderProductionIngredientRequest:
    """Request payload for updating ingredient consumption data in a manufacturing order production batch

    Example:
        {'batch_transactions': [{'batch_id': 123, 'quantity': 3.2}]}
    """

    batch_transactions: list[BatchTransaction] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction import BatchTransaction

        d = dict(src_dict)
        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransaction] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransaction.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        update_manufacturing_order_production_ingredient_request = cls(
            batch_transactions=batch_transactions,
        )

        update_manufacturing_order_production_ingredient_request.additional_properties = d
        return update_manufacturing_order_production_ingredient_request

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
