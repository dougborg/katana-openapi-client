import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.stock_transfer_status import StockTransferStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="StockTransfer")


@_attrs_define
class StockTransfer:
    id: int
    reference_no: str
    from_location_id: int
    to_location_id: int
    status: Unset | StockTransferStatus = UNSET
    transfer_date: Unset | datetime.datetime = UNSET
    additional_info: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        reference_no = self.reference_no

        from_location_id = self.from_location_id

        to_location_id = self.to_location_id

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        transfer_date: Unset | str = UNSET
        if not isinstance(self.transfer_date, Unset):
            transfer_date = self.transfer_date.isoformat()

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "reference_no": reference_no,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if transfer_date is not UNSET:
            field_dict["transfer_date"] = transfer_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        reference_no = d.pop("reference_no")

        from_location_id = d.pop("from_location_id")

        to_location_id = d.pop("to_location_id")

        _status = d.pop("status", UNSET)
        status: Unset | StockTransferStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StockTransferStatus(_status)

        _transfer_date = d.pop("transfer_date", UNSET)
        transfer_date: Unset | datetime.datetime
        if isinstance(_transfer_date, Unset):
            transfer_date = UNSET
        else:
            transfer_date = isoparse(_transfer_date)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        stock_transfer = cls(
            id=id,
            reference_no=reference_no,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            status=status,
            transfer_date=transfer_date,
            additional_info=additional_info,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        stock_transfer.additional_properties = d
        return stock_transfer

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
