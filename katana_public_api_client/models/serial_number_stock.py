from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.serial_number_stock_transactions_item import (
        SerialNumberStockTransactionsItem,
    )


T = TypeVar("T", bound="SerialNumberStock")


@_attrs_define
class SerialNumberStock:
    """Current stock status and transaction history of individual serialized inventory items"""

    id: str
    serial_number: str
    in_stock: bool
    transactions: list["SerialNumberStockTransactionsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        serial_number = self.serial_number

        in_stock = self.in_stock

        transactions = []
        for transactions_item_data in self.transactions:
            transactions_item = transactions_item_data.to_dict()
            transactions.append(transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "serial_number": serial_number,
                "in_stock": in_stock,
                "transactions": transactions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.serial_number_stock_transactions_item import (
            SerialNumberStockTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        serial_number = d.pop("serial_number")

        in_stock = d.pop("in_stock")

        transactions = []
        _transactions = d.pop("transactions")
        for transactions_item_data in _transactions:
            transactions_item = SerialNumberStockTransactionsItem.from_dict(
                transactions_item_data
            )

            transactions.append(transactions_item)

        serial_number_stock = cls(
            id=id,
            serial_number=serial_number,
            in_stock=in_stock,
            transactions=transactions,
        )

        serial_number_stock.additional_properties = d
        return serial_number_stock

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
