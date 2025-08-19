import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="ManufacturingOrderOperationProduction")


@_attrs_define
class ManufacturingOrderOperationProduction:
    """Record of actual work performed on a specific operation during manufacturing order production"""

    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | str = UNSET
    id: Unset | int = UNSET
    location_id: Unset | int = UNSET
    manufacturing_order_id: Unset | int = UNSET
    manufacturing_order_operation_id: Unset | int = UNSET
    production_id: Unset | int = UNSET
    time: Unset | float = UNSET
    production_date: Unset | datetime.datetime = UNSET
    cost: Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        id = self.id

        location_id = self.location_id

        manufacturing_order_id = self.manufacturing_order_id

        manufacturing_order_operation_id = self.manufacturing_order_operation_id

        production_id = self.production_id

        time = self.time

        production_date: Unset | str = UNSET
        if not isinstance(self.production_date, Unset):
            production_date = self.production_date.isoformat()

        cost = self.cost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if id is not UNSET:
            field_dict["id"] = id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if manufacturing_order_id is not UNSET:
            field_dict["manufacturing_order_id"] = manufacturing_order_id
        if manufacturing_order_operation_id is not UNSET:
            field_dict["manufacturing_order_operation_id"] = (
                manufacturing_order_operation_id
            )
        if production_id is not UNSET:
            field_dict["production_id"] = production_id
        if time is not UNSET:
            field_dict["time"] = time
        if production_date is not UNSET:
            field_dict["production_date"] = production_date
        if cost is not UNSET:
            field_dict["cost"] = cost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
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

        id = d.pop("id", UNSET)

        location_id = d.pop("location_id", UNSET)

        manufacturing_order_id = d.pop("manufacturing_order_id", UNSET)

        manufacturing_order_operation_id = d.pop(
            "manufacturing_order_operation_id", UNSET
        )

        production_id = d.pop("production_id", UNSET)

        time = d.pop("time", UNSET)

        _production_date = d.pop("production_date", UNSET)
        production_date: Unset | datetime.datetime
        if isinstance(_production_date, Unset):
            production_date = UNSET
        else:
            production_date = isoparse(_production_date)

        cost = d.pop("cost", UNSET)

        manufacturing_order_operation_production = cls(
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            id=id,
            location_id=location_id,
            manufacturing_order_id=manufacturing_order_id,
            manufacturing_order_operation_id=manufacturing_order_operation_id,
            production_id=production_id,
            time=time,
            production_date=production_date,
            cost=cost,
        )

        manufacturing_order_operation_production.additional_properties = d
        return manufacturing_order_operation_production

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
