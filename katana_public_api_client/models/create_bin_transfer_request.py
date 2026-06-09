from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bin_transfer_row_create_nested import BinTransferRowCreateNested


T = TypeVar("T", bound="CreateBinTransferRequest")


@_attrs_define
class CreateBinTransferRequest:
    """Request payload for creating a bin transfer, optionally with rows and per-row
    traceability in a single call.

        Example:
            {'location_id': 1, 'bin_transfer_number': 'BT-1', 'additional_info': 'urgent transfer', 'bin_transfer_rows':
                [{'variant_id': 42, 'quantity': '3', 'source_bin_location_id': 7, 'target_bin_location_id': 9, 'traceability':
                [{'batch_id': 100, 'quantity': '3'}]}]}
    """

    location_id: int
    bin_transfer_number: str | Unset = UNSET
    additional_info: None | str | Unset = UNSET
    created_date: datetime.datetime | Unset = UNSET
    bin_transfer_rows: list[BinTransferRowCreateNested] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        bin_transfer_number = self.bin_transfer_number

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        created_date: str | Unset = UNSET
        if not isinstance(self.created_date, Unset):
            created_date = self.created_date.isoformat()

        bin_transfer_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.bin_transfer_rows, Unset):
            bin_transfer_rows = []
            for bin_transfer_rows_item_data in self.bin_transfer_rows:
                bin_transfer_rows_item = bin_transfer_rows_item_data.to_dict()
                bin_transfer_rows.append(bin_transfer_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "location_id": location_id,
            }
        )
        if bin_transfer_number is not UNSET:
            field_dict["bin_transfer_number"] = bin_transfer_number
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if bin_transfer_rows is not UNSET:
            field_dict["bin_transfer_rows"] = bin_transfer_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_transfer_row_create_nested import BinTransferRowCreateNested

        d = dict(src_dict)
        location_id = d.pop("location_id")

        bin_transfer_number = d.pop("bin_transfer_number", UNSET)

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        _created_date = d.pop("created_date", UNSET)
        created_date: datetime.datetime | Unset
        if isinstance(_created_date, Unset):
            created_date = UNSET
        else:
            created_date = datetime.datetime.fromisoformat(_created_date)

        _bin_transfer_rows = d.pop("bin_transfer_rows", UNSET)
        bin_transfer_rows: list[BinTransferRowCreateNested] | Unset = UNSET
        if _bin_transfer_rows is not UNSET:
            bin_transfer_rows = []
            for bin_transfer_rows_item_data in _bin_transfer_rows:
                bin_transfer_rows_item = BinTransferRowCreateNested.from_dict(
                    cast(Mapping[str, Any], bin_transfer_rows_item_data)
                )

                bin_transfer_rows.append(bin_transfer_rows_item)

        create_bin_transfer_request = cls(
            location_id=location_id,
            bin_transfer_number=bin_transfer_number,
            additional_info=additional_info,
            created_date=created_date,
            bin_transfer_rows=bin_transfer_rows,
        )

        return create_bin_transfer_request
