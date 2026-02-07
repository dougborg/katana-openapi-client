from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_stock_transfer_status_request_status import (
    UpdateStockTransferStatusRequestStatus,
)

T = TypeVar("T", bound="UpdateStockTransferStatusRequest")


@_attrs_define
class UpdateStockTransferStatusRequest:
    """Request payload for updating a stock transfer status"""

    status: UpdateStockTransferStatusRequestStatus

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
        status = UpdateStockTransferStatusRequestStatus(d.pop("status"))

        update_stock_transfer_status_request = cls(
            status=status,
        )

        return update_stock_transfer_status_request
