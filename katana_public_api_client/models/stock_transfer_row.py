from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_transfer_row_batch_transactions_item import (
        StockTransferRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="StockTransferRow")


@_attrs_define
class StockTransferRow:
    """Line item in a stock transfer showing the product variant and quantity being moved

    Attributes:
        variant_id (int): ID of the product or material variant being transferred
        quantity (float): Quantity of the variant being transferred
        id (Union[Unset, int]): Unique identifier for the stock transfer row
        batch_transactions (Union[Unset, list['StockTransferRowBatchTransactionsItem']]): Batch transaction details for
            batch-tracked items
    """

    variant_id: int
    quantity: float
    id: Unset | int = UNSET
    batch_transactions: Unset | list["StockTransferRowBatchTransactionsItem"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

        id = self.id

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stock_transfer_row_batch_transactions_item import (
            StockTransferRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        id = d.pop("id", UNSET)

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = StockTransferRowBatchTransactionsItem.from_dict(
                batch_transactions_item_data
            )

            batch_transactions.append(batch_transactions_item)

        stock_transfer_row = cls(
            variant_id=variant_id,
            quantity=quantity,
            id=id,
            batch_transactions=batch_transactions,
        )

        stock_transfer_row.additional_properties = d
        return stock_transfer_row

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
