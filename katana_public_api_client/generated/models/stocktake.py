import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.stocktake_status import StocktakeStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Stocktake")


@_attrs_define
class Stocktake:
    id: int
    reference_no: str
    location_id: int
    status: StocktakeStatus
    stocktake_date: Unset | datetime.datetime = UNSET
    notes: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        reference_no = self.reference_no

        location_id = self.location_id

        status = self.status.value

        stocktake_date: Unset | str = UNSET
        if not isinstance(self.stocktake_date, Unset):
            stocktake_date = self.stocktake_date.isoformat()

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "reference_no": reference_no,
                "location_id": location_id,
                "status": status,
            }
        )
        if stocktake_date is not UNSET:
            field_dict["stocktake_date"] = stocktake_date
        if notes is not UNSET:
            field_dict["notes"] = notes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        reference_no = d.pop("reference_no")

        location_id = d.pop("location_id")

        status = StocktakeStatus(d.pop("status"))

        _stocktake_date = d.pop("stocktake_date", UNSET)
        stocktake_date: Unset | datetime.datetime
        if isinstance(_stocktake_date, Unset):
            stocktake_date = UNSET
        else:
            stocktake_date = isoparse(_stocktake_date)

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

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

        stocktake = cls(
            id=id,
            reference_no=reference_no,
            location_id=location_id,
            status=status,
            stocktake_date=stocktake_date,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )

        stocktake.additional_properties = d
        return stocktake

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
