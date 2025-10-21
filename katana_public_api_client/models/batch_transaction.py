from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="BatchTransaction")


@_attrs_define
class BatchTransaction:
    """Represents a quantity transaction for a specific batch in manufacturing, sales, or inventory operations

    Example:
        {'batch_id': 1109, 'quantity': 25.0}

    Attributes:
        batch_id (int): ID of the batch for the transaction
        quantity (float): The quantity in this batch transaction
    """

    batch_id: int
    quantity: float

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

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

        batch_transaction = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        return batch_transaction
