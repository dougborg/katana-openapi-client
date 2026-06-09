from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.bin_transfer_status import BinTransferStatus

if TYPE_CHECKING:
    from ..models.bin_transfer_row import BinTransferRow


T = TypeVar("T", bound="BinTransfer")


@_attrs_define
class BinTransfer:
    """A movement of stock between bins within a single location, optionally carrying
    per-row batch/serial traceability.

        Example:
            {'id': 1, 'bin_transfer_number': 'BT-1', 'location_id': 1, 'status': 'IN_TRANSIT', 'created_date':
                '2026-05-22T10:00:00.000Z', 'departed_at': '2026-05-22T11:00:00.000Z', 'arrived_at': None, 'additional_info':
                'urgent transfer', 'bin_transfer_rows': [{'id': 11, 'bin_transfer_id': 1, 'location_id': 1, 'variant_id': 42,
                'quantity': '3', 'source_bin_location_id': 7, 'target_bin_location_id': 9, 'traceability': [{'batch_id': 100,
                'serial_number_id': None, 'quantity': '3'}], 'created_at': '2026-05-22T10:00:00.000Z', 'updated_at':
                '2026-05-22T10:00:00.000Z', 'deleted_at': None}], 'created_at': '2026-05-22T10:00:00.000Z', 'updated_at':
                '2026-05-22T10:00:00.000Z', 'deleted_at': None}
    """

    id: int
    bin_transfer_number: str
    location_id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    status: BinTransferStatus | Unset = UNSET
    created_date: datetime.datetime | None | Unset = UNSET
    departed_at: datetime.datetime | None | Unset = UNSET
    arrived_at: datetime.datetime | None | Unset = UNSET
    additional_info: None | str | Unset = UNSET
    bin_transfer_rows: list[BinTransferRow] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        bin_transfer_number = self.bin_transfer_number

        location_id = self.location_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        created_date: None | str | Unset
        if isinstance(self.created_date, Unset):
            created_date = UNSET
        elif isinstance(self.created_date, datetime.datetime):
            created_date = self.created_date.isoformat()
        else:
            created_date = self.created_date

        departed_at: None | str | Unset
        if isinstance(self.departed_at, Unset):
            departed_at = UNSET
        elif isinstance(self.departed_at, datetime.datetime):
            departed_at = self.departed_at.isoformat()
        else:
            departed_at = self.departed_at

        arrived_at: None | str | Unset
        if isinstance(self.arrived_at, Unset):
            arrived_at = UNSET
        elif isinstance(self.arrived_at, datetime.datetime):
            arrived_at = self.arrived_at.isoformat()
        else:
            arrived_at = self.arrived_at

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        bin_transfer_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.bin_transfer_rows, Unset):
            bin_transfer_rows = []
            for bin_transfer_rows_item_data in self.bin_transfer_rows:
                bin_transfer_rows_item = bin_transfer_rows_item_data.to_dict()
                bin_transfer_rows.append(bin_transfer_rows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bin_transfer_number": bin_transfer_number,
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
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if departed_at is not UNSET:
            field_dict["departed_at"] = departed_at
        if arrived_at is not UNSET:
            field_dict["arrived_at"] = arrived_at
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if bin_transfer_rows is not UNSET:
            field_dict["bin_transfer_rows"] = bin_transfer_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_transfer_row import BinTransferRow

        d = dict(src_dict)
        id = d.pop("id")

        bin_transfer_number = d.pop("bin_transfer_number")

        location_id = d.pop("location_id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = datetime.datetime.fromisoformat(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        _status = d.pop("status", UNSET)
        status: BinTransferStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = BinTransferStatus(_status)

        def _parse_created_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_date_type_0 = datetime.datetime.fromisoformat(data)

                return created_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_date = _parse_created_date(d.pop("created_date", UNSET))

        def _parse_departed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                departed_at_type_0 = datetime.datetime.fromisoformat(data)

                return departed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        departed_at = _parse_departed_at(d.pop("departed_at", UNSET))

        def _parse_arrived_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                arrived_at_type_0 = datetime.datetime.fromisoformat(data)

                return arrived_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        arrived_at = _parse_arrived_at(d.pop("arrived_at", UNSET))

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        _bin_transfer_rows = d.pop("bin_transfer_rows", UNSET)
        bin_transfer_rows: list[BinTransferRow] | Unset = UNSET
        if _bin_transfer_rows is not UNSET:
            bin_transfer_rows = []
            for bin_transfer_rows_item_data in _bin_transfer_rows:
                bin_transfer_rows_item = BinTransferRow.from_dict(
                    cast(Mapping[str, Any], bin_transfer_rows_item_data)
                )

                bin_transfer_rows.append(bin_transfer_rows_item)

        bin_transfer = cls(
            id=id,
            bin_transfer_number=bin_transfer_number,
            location_id=location_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            status=status,
            created_date=created_date,
            departed_at=departed_at,
            arrived_at=arrived_at,
            additional_info=additional_info,
            bin_transfer_rows=bin_transfer_rows,
        )

        bin_transfer.additional_properties = d
        return bin_transfer

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
