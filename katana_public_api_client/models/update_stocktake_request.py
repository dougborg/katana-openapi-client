from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.update_stocktake_request_status import UpdateStocktakeRequestStatus

T = TypeVar("T", bound="UpdateStocktakeRequest")


@_attrs_define
class UpdateStocktakeRequest:
    """Request payload for updating an existing stocktake

    Example:
        {'stocktake_number': 'STK-2024-003', 'location_id': 1, 'reason': 'Quarterly inventory count - updated',
            'status': 'IN_PROGRESS'}
    """

    stocktake_number: str | Unset = UNSET
    location_id: int | Unset = UNSET
    reason: str | Unset = UNSET
    status: UpdateStocktakeRequestStatus | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_number = self.stocktake_number

        location_id = self.location_id

        reason = self.reason

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if stocktake_number is not UNSET:
            field_dict["stocktake_number"] = stocktake_number
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if reason is not UNSET:
            field_dict["reason"] = reason
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stocktake_number = d.pop("stocktake_number", UNSET)

        location_id = d.pop("location_id", UNSET)

        reason = d.pop("reason", UNSET)

        _status = d.pop("status", UNSET)
        status: UpdateStocktakeRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateStocktakeRequestStatus(_status)

        update_stocktake_request = cls(
            stocktake_number=stocktake_number,
            location_id=location_id,
            reason=reason,
            status=status,
        )

        return update_stocktake_request
