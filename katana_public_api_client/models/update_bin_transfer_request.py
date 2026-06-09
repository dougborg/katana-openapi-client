from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateBinTransferRequest")


@_attrs_define
class UpdateBinTransferRequest:
    """Request payload for updating a bin transfer's header fields.

    Example:
        {'bin_transfer_number': 'BT-1', 'additional_info': 'updated note'}
    """

    bin_transfer_number: str | Unset = UNSET
    location_id: int | Unset = UNSET
    additional_info: None | str | Unset = UNSET
    created_date: datetime.datetime | None | Unset = UNSET
    departed_at: datetime.datetime | None | Unset = UNSET
    arrived_at: datetime.datetime | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        bin_transfer_number = self.bin_transfer_number

        location_id = self.location_id

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

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

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if bin_transfer_number is not UNSET:
            field_dict["bin_transfer_number"] = bin_transfer_number
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if departed_at is not UNSET:
            field_dict["departed_at"] = departed_at
        if arrived_at is not UNSET:
            field_dict["arrived_at"] = arrived_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bin_transfer_number = d.pop("bin_transfer_number", UNSET)

        location_id = d.pop("location_id", UNSET)

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

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

        update_bin_transfer_request = cls(
            bin_transfer_number=bin_transfer_number,
            location_id=location_id,
            additional_info=additional_info,
            created_date=created_date,
            departed_at=departed_at,
            arrived_at=arrived_at,
        )

        return update_bin_transfer_request
