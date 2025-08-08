import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location_address import LocationAddress


T = TypeVar("T", bound="Location")


@_attrs_define
class Location:
    """
    Example:
        {'data': [{'id': 101, 'name': 'Main Warehouse - Brooklyn', 'legal_name': 'Acme Manufacturing Co. - Brooklyn
            Facility', 'address_id': 1001, 'address': {'id': 1001, 'city': 'Brooklyn', 'country': 'United States', 'line_1':
            '500 Industrial Park Drive', 'line_2': 'Building A', 'state': 'New York', 'zip': '11201'}, 'is_primary': True,
            'sales_allowed': True, 'purchase_allowed': True, 'manufacturing_allowed': True, 'created_at':
            '2020-10-23T10:37:05.085Z', 'updated_at': '2024-01-15T09:30:00.000Z', 'deleted_at': None}, {'id': 102, 'name':
            'Distribution Center - Miami', 'legal_name': 'Acme Manufacturing Co. - Miami DC', 'address_id': 1002, 'address':
            {'id': 1002, 'city': 'Miami', 'country': 'United States', 'line_1': '750 Commerce Boulevard', 'line_2': 'Suite
            200', 'state': 'Florida', 'zip': '33126'}, 'is_primary': False, 'sales_allowed': True, 'purchase_allowed':
            False, 'manufacturing_allowed': False, 'created_at': '2020-11-15T14:22:15.000Z', 'updated_at':
            '2024-01-10T11:15:30.000Z', 'deleted_at': None}, {'id': 103, 'name': 'West Coast Production', 'legal_name':
            'Acme Manufacturing Co. - California Plant', 'address_id': None, 'address': None, 'is_primary': False,
            'sales_allowed': False, 'purchase_allowed': True, 'manufacturing_allowed': True, 'created_at':
            '2021-03-01T08:00:00.000Z', 'updated_at': '2024-01-05T16:45:22.000Z', 'deleted_at': None}]}
    """

    id: int
    name: str
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    legal_name: Unset | str = UNSET
    address_id: Unset | int = UNSET
    address: Union[Unset, "LocationAddress"] = UNSET
    is_primary: Unset | bool = UNSET
    sales_allowed: Unset | bool = UNSET
    purchase_allowed: Unset | bool = UNSET
    manufacturing_allowed: Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

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

        legal_name = self.legal_name

        address_id = self.address_id

        address: Unset | dict[str, Any] = UNSET
        if not isinstance(self.address, Unset):
            address = self.address.to_dict()

        is_primary = self.is_primary

        sales_allowed = self.sales_allowed

        purchase_allowed = self.purchase_allowed

        manufacturing_allowed = self.manufacturing_allowed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if legal_name is not UNSET:
            field_dict["legal_name"] = legal_name
        if address_id is not UNSET:
            field_dict["address_id"] = address_id
        if address is not UNSET:
            field_dict["address"] = address
        if is_primary is not UNSET:
            field_dict["is_primary"] = is_primary
        if sales_allowed is not UNSET:
            field_dict["sales_allowed"] = sales_allowed
        if purchase_allowed is not UNSET:
            field_dict["purchase_allowed"] = purchase_allowed
        if manufacturing_allowed is not UNSET:
            field_dict["manufacturing_allowed"] = manufacturing_allowed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.location_address import LocationAddress

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

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

        legal_name = d.pop("legal_name", UNSET)

        address_id = d.pop("address_id", UNSET)

        _address = d.pop("address", UNSET)
        address: Unset | LocationAddress
        if isinstance(_address, Unset):
            address = UNSET
        else:
            address = LocationAddress.from_dict(_address)

        is_primary = d.pop("is_primary", UNSET)

        sales_allowed = d.pop("sales_allowed", UNSET)

        purchase_allowed = d.pop("purchase_allowed", UNSET)

        manufacturing_allowed = d.pop("manufacturing_allowed", UNSET)

        location = cls(
            id=id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            legal_name=legal_name,
            address_id=address_id,
            address=address,
            is_primary=is_primary,
            sales_allowed=sales_allowed,
            purchase_allowed=purchase_allowed,
            manufacturing_allowed=manufacturing_allowed,
        )

        location.additional_properties = d
        return location

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
