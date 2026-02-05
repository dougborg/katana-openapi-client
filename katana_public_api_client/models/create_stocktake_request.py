from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.create_stocktake_request_status import CreateStocktakeRequestStatus

T = TypeVar("T", bound="CreateStocktakeRequest")


@_attrs_define
class CreateStocktakeRequest:
    """Request payload for creating a new stocktake to perform physical inventory counting

    Example:
        {'stocktake_number': 'STK-2024-003', 'location_id': 1, 'reason': 'Quarterly inventory count', 'status':
            'NOT_STARTED'}
    """

    stocktake_number: str
    location_id: int
    reason: str | Unset = UNSET
    status: CreateStocktakeRequestStatus | Unset = (
        CreateStocktakeRequestStatus.NOT_STARTED
    )

    def to_dict(self) -> dict[str, Any]:
        stocktake_number = self.stocktake_number

        location_id = self.location_id

        reason = self.reason

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stocktake_number": stocktake_number,
                "location_id": location_id,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stocktake_number = d.pop("stocktake_number")

        location_id = d.pop("location_id")

        reason = d.pop("reason", UNSET)

        _status = d.pop("status", UNSET)
        status: CreateStocktakeRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreateStocktakeRequestStatus(_status)

        create_stocktake_request = cls(
            stocktake_number=stocktake_number,
            location_id=location_id,
            reason=reason,
            status=status,
        )

        return create_stocktake_request
