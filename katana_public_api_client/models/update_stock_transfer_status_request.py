from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.stock_transfer_status import StockTransferStatus

T = TypeVar("T", bound="UpdateStockTransferStatusRequest")


@_attrs_define
class UpdateStockTransferStatusRequest:
    """Request payload for updating a stock transfer status"""

    status: StockTransferStatus | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: StockTransferStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StockTransferStatus(_status)

        update_stock_transfer_status_request = cls(
            status=status,
        )

        return update_stock_transfer_status_request
