from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="LocationAddress")


@_attrs_define
class LocationAddress:
    id: int
    city: str
    country: str
    line_1: str
    state: str
    zip_: str
    line_2: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        city = self.city

        country = self.country

        line_1 = self.line_1

        state = self.state

        zip_ = self.zip_

        line_2 = self.line_2

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "city": city,
                "country": country,
                "line_1": line_1,
                "state": state,
                "zip": zip_,
            }
        )
        if line_2 is not UNSET:
            field_dict["line_2"] = line_2

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        city = d.pop("city")

        country = d.pop("country")

        line_1 = d.pop("line_1")

        state = d.pop("state")

        zip_ = d.pop("zip")

        line_2 = d.pop("line_2", UNSET)

        location_address = cls(
            id=id,
            city=city,
            country=country,
            line_1=line_1,
            state=state,
            zip_=zip_,
            line_2=line_2,
        )

        location_address.additional_properties = d
        return location_address

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
