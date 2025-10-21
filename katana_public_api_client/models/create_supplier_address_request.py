from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSupplierAddressRequest")


@_attrs_define
class CreateSupplierAddressRequest:
    """Request payload for creating a new address for an existing supplier

    Example:
        {'supplier_id': 4001, 'line_1': '856 Distribution Center Dr', 'line_2': None, 'city': 'Milwaukee', 'state':
            'WI', 'zip': '53218', 'country': 'US'}

    Attributes:
        supplier_id (int): Unique identifier of the supplier this address belongs to
        line_1 (str): Primary address line (street number, street name)
        line_2 (Union[None, Unset, str]): Secondary address line (suite, apartment, building)
        city (Union[None, Unset, str]): City name
        state (Union[None, Unset, str]): State, province, or region
        zip_ (Union[None, Unset, str]): Postal code or ZIP code
        country (Union[None, Unset, str]): Country code (ISO 3166-1 alpha-2 format)
    """

    supplier_id: int
    line_1: str
    line_2: None | Unset | str = UNSET
    city: None | Unset | str = UNSET
    state: None | Unset | str = UNSET
    zip_: None | Unset | str = UNSET
    country: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
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

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "supplier_id": supplier_id,
                "line_1": line_1,
            }
        )
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
        supplier_id = d.pop("supplier_id")

        line_1 = d.pop("line_1")

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

        create_supplier_address_request = cls(
            supplier_id=supplier_id,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
        )

        return create_supplier_address_request
