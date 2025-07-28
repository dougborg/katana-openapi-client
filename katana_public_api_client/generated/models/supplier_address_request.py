from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="SupplierAddressRequest")


@_attrs_define
class SupplierAddressRequest:
    line_1: str
    supplier_id: Unset | int = UNSET
    line_2: Unset | str = UNSET
    city: Unset | str = UNSET
    state: Unset | str = UNSET
    zip_: Unset | str = UNSET
    country: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        line_1 = self.line_1

        supplier_id = self.supplier_id

        line_2 = self.line_2

        city = self.city

        state = self.state

        zip_ = self.zip_

        country = self.country

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "line_1": line_1,
            }
        )
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        line_1 = d.pop("line_1")

        supplier_id = d.pop("supplier_id", UNSET)

        line_2 = d.pop("line_2", UNSET)

        city = d.pop("city", UNSET)

        state = d.pop("state", UNSET)

        zip_ = d.pop("zip", UNSET)

        country = d.pop("country", UNSET)

        supplier_address_request = cls(
            line_1=line_1,
            supplier_id=supplier_id,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
        )

        return supplier_address_request
