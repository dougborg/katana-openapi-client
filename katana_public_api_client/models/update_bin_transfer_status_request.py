from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.bin_transfer_status import BinTransferStatus

T = TypeVar("T", bound="UpdateBinTransferStatusRequest")


@_attrs_define
class UpdateBinTransferStatusRequest:
    """Request payload for changing a bin transfer's status.

    Example:
        {'status': 'IN_TRANSIT'}
    """

    status: BinTransferStatus

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
        status = BinTransferStatus(d.pop("status"))

        update_bin_transfer_status_request = cls(
            status=status,
        )

        return update_bin_transfer_status_request
