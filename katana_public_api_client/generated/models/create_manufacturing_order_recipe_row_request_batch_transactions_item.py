from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem")


@_attrs_define
class CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem:
    batch_id: int
    quantity: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "batch_id": batch_id,
                "quantity": quantity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id")

        quantity = d.pop("quantity")

        create_manufacturing_order_recipe_row_request_batch_transactions_item = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        create_manufacturing_order_recipe_row_request_batch_transactions_item.additional_properties = d
        return create_manufacturing_order_recipe_row_request_batch_transactions_item

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
