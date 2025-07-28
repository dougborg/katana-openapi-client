from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateSupplierAddressRequest")


@_attrs_define
class UpdateSupplierAddressRequest:
    line_1: None | Unset | str = UNSET
    line_2: None | Unset | str = UNSET
    city: None | Unset | str = UNSET
    state: None | Unset | str = UNSET
    zip_: None | Unset | str = UNSET
    country: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        line_1: None | Unset | str
        if isinstance(self.line_1, Unset):
            line_1 = UNSET
        else:
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

        field_dict: dict[str, Any] = {}

        field_dict.update({})
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_line_1(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        line_1 = _parse_line_1(d.pop("line_1", UNSET))

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

        update_supplier_address_request = cls(
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
        )

        return update_supplier_address_request
