import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

T = TypeVar("T", bound="SerialNumberStockTransactionsItem")


@_attrs_define
class SerialNumberStockTransactionsItem:
    """
    Attributes:
        id (str): Transaction ID
        resource_id (int): Resource ID associated with transaction
        resource_type (str): Type of resource (ManufacturingOrder, etc.)
        transaction_date (datetime.datetime): Date and time of transaction
        quantity_change (int): Quantity change in transaction
    """

    id: str
    resource_id: int
    resource_type: str
    transaction_date: datetime.datetime
    quantity_change: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        resource_id = self.resource_id

        resource_type = self.resource_type

        transaction_date = self.transaction_date.isoformat()

        quantity_change = self.quantity_change

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "resource_id": resource_id,
                "resource_type": resource_type,
                "transaction_date": transaction_date,
                "quantity_change": quantity_change,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        resource_id = d.pop("resource_id")

        resource_type = d.pop("resource_type")

        transaction_date = isoparse(d.pop("transaction_date"))

        quantity_change = d.pop("quantity_change")

        serial_number_stock_transactions_item = cls(
            id=id,
            resource_id=resource_id,
            resource_type=resource_type,
            transaction_date=transaction_date,
            quantity_change=quantity_change,
        )

        serial_number_stock_transactions_item.additional_properties = d
        return serial_number_stock_transactions_item

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
