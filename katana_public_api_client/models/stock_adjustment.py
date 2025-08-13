import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.stock_adjustment_status import StockAdjustmentStatus

T = TypeVar("T", bound="StockAdjustment")


@_attrs_define
class StockAdjustment:
    """Manual inventory adjustment record for correcting stock discrepancies and maintaining accurate inventory levels

    Example:
        {'id': 2001, 'reference_no': 'SA-2024-001', 'location_id': 1, 'status': 'COMPLETED', 'adjustment_date':
            '2024-01-15T14:30:00.000Z', 'additional_info': 'Physical count discrepancy correction', 'created_at':
            '2024-01-15T14:30:00.000Z', 'updated_at': '2024-01-15T14:30:00.000Z', 'deleted_at': None}
    """

    id: int
    reference_no: str
    location_id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | str = UNSET
    status: Unset | StockAdjustmentStatus = UNSET
    adjustment_date: Unset | datetime.datetime = UNSET
    additional_info: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        reference_no = self.reference_no

        location_id = self.location_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = self.deleted_at

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        adjustment_date: Unset | str = UNSET
        if not isinstance(self.adjustment_date, Unset):
            adjustment_date = self.adjustment_date.isoformat()

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "reference_no": reference_no,
                "location_id": location_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if status is not UNSET:
            field_dict["status"] = status
        if adjustment_date is not UNSET:
            field_dict["adjustment_date"] = adjustment_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        reference_no = d.pop("reference_no")

        location_id = d.pop("location_id")

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        _status = d.pop("status", UNSET)
        status: Unset | StockAdjustmentStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StockAdjustmentStatus(_status)

        _adjustment_date = d.pop("adjustment_date", UNSET)
        adjustment_date: Unset | datetime.datetime
        if isinstance(_adjustment_date, Unset):
            adjustment_date = UNSET
        else:
            adjustment_date = isoparse(_adjustment_date)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        stock_adjustment = cls(
            id=id,
            reference_no=reference_no,
            location_id=location_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            status=status,
            adjustment_date=adjustment_date,
            additional_info=additional_info,
        )

        stock_adjustment.additional_properties = d
        return stock_adjustment

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
