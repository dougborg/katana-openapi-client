from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.update_customer_address_body_entity_type import (
    UpdateCustomerAddressBodyEntityType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCustomerAddressBody")


@_attrs_define
class UpdateCustomerAddressBody:
    entity_type: Unset | UpdateCustomerAddressBodyEntityType = UNSET
    first_name: None | Unset | str = UNSET
    last_name: None | Unset | str = UNSET
    company: None | Unset | str = UNSET
    phone: None | Unset | str = UNSET
    line_1: None | Unset | str = UNSET
    line_2: None | Unset | str = UNSET
    city: None | Unset | str = UNSET
    state: None | Unset | str = UNSET
    zip_: None | Unset | str = UNSET
    country: None | Unset | str = UNSET
    is_default: Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        entity_type: Unset | str = UNSET
        if not isinstance(self.entity_type, Unset):
            entity_type = self.entity_type.value

        first_name: None | Unset | str
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: None | Unset | str
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        company: None | Unset | str
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        phone: None | Unset | str
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

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

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
        if phone is not UNSET:
            field_dict["phone"] = phone
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
        if is_default is not UNSET:
            field_dict["is_default"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _entity_type = d.pop("entity_type", UNSET)
        entity_type: Unset | UpdateCustomerAddressBodyEntityType
        if isinstance(_entity_type, Unset):
            entity_type = UNSET
        else:
            entity_type = UpdateCustomerAddressBodyEntityType(_entity_type)

        def _parse_first_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_company(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_phone(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        phone = _parse_phone(d.pop("phone", UNSET))

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

        is_default = d.pop("is_default", UNSET)

        update_customer_address_body = cls(
            entity_type=entity_type,
            first_name=first_name,
            last_name=last_name,
            company=company,
            phone=phone,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            is_default=is_default,
        )

        update_customer_address_body.additional_properties = d
        return update_customer_address_body

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
