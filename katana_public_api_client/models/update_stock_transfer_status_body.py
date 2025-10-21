from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_stock_transfer_status_body_status import (
    UpdateStockTransferStatusBodyStatus,
)

T = TypeVar("T", bound="UpdateStockTransferStatusBody")


@_attrs_define
class UpdateStockTransferStatusBody:
    """
    Attributes:
        status (UpdateStockTransferStatusBodyStatus): New status for the stock transfer
    """

    status: UpdateStockTransferStatusBodyStatus

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = UpdateStockTransferStatusBodyStatus(d.pop("status"))

        update_stock_transfer_status_body = cls(
            status=status,
        )

        return update_stock_transfer_status_body
