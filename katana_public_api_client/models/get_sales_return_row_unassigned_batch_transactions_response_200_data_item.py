from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar(
    "T", bound="GetSalesReturnRowUnassignedBatchTransactionsResponse200DataItem"
)


@_attrs_define
class GetSalesReturnRowUnassignedBatchTransactionsResponse200DataItem:
    """
    Attributes:
        id (Union[Unset, int]): Batch transaction ID
        batch_id (Union[Unset, int]): Batch ID
        quantity (Union[Unset, float]): Transaction quantity
        status (Union[Unset, str]): Transaction status
    """

    id: Unset | int = UNSET
    batch_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    status: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        batch_id = self.batch_id

        quantity = self.quantity

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        batch_id = d.pop("batch_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        status = d.pop("status", UNSET)

        get_sales_return_row_unassigned_batch_transactions_response_200_data_item = cls(
            id=id,
            batch_id=batch_id,
            quantity=quantity,
            status=status,
        )

        get_sales_return_row_unassigned_batch_transactions_response_200_data_item.additional_properties = d
        return get_sales_return_row_unassigned_batch_transactions_response_200_data_item

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
