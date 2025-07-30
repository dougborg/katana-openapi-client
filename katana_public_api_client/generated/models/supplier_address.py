import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SupplierAddress")


@_attrs_define
class SupplierAddress:
    id: Unset | int = UNSET
    supplier_id: Unset | int = UNSET
    line_1: Unset | str = UNSET
    line_2: None | Unset | str = UNSET
    city: None | Unset | str = UNSET
    state: None | Unset | str = UNSET
    zip_: None | Unset | str = UNSET
    country: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        supplier_id = self.supplier_id

        line_1 = self.line_1

        line_2: None | Unset | str
        if isinstance(self.line_2, Unset):
            line_2 = UNSET
        else:
            line_2 = self.line_2

        city: None | Unset | str
        if isinstance(self.city, Unset):
            city = UNSET
        else:
            city = self.city

        state: None | Unset | str
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        zip_: None | Unset | str
        if isinstance(self.zip_, Unset):
            zip_ = UNSET
        else:
            zip_ = self.zip_

        country: None | Unset | str
        if isinstance(self.country, Unset):
            country = UNSET
        else:
            country = self.country

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
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
        if line_1 is not UNSET:
            field_dict["line_1"] = line_1
        if line_2 is not UNSET:
            field_dict["line_2"] = line_2
        if city is not UNSET:
            field_dict["city"] = city
        if state is not UNSET:
            field_dict["state"] = state
        if zip_ is not UNSET:
            field_dict["zip"] = zip_
        if country is not UNSET:
            field_dict["country"] = country
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
        id = d.pop("id", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        line_1 = d.pop("line_1", UNSET)

        def _parse_line_2(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        line_2 = _parse_line_2(d.pop("line_2", UNSET))

        def _parse_city(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        city = _parse_city(d.pop("city", UNSET))

        def _parse_state(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        state = _parse_state(d.pop("state", UNSET))

        def _parse_zip_(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        zip_ = _parse_zip_(d.pop("zip", UNSET))

        def _parse_country(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        country = _parse_country(d.pop("country", UNSET))

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

        supplier_address = cls(
            id=id,
            supplier_id=supplier_id,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        supplier_address.additional_properties = d
        return supplier_address

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
