from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location_address import LocationAddress


T = TypeVar("T", bound="Location")


@_attrs_define
class Location:
    """Manufacturing location or warehouse facility where inventory is managed and operations are performed

    Example:
        {'id': 1, 'name': 'Main location', 'legal_name': 'Amazon', 'address_id': 1, 'address': {'id': 1, 'city': 'New
            York', 'country': 'US', 'line_1': '10 East 20th Example St', 'line_2': '', 'state': 'New York', 'zip': '10000'},
            'is_primary': True, 'sales_allowed': True, 'purchase_allowed': True, 'manufacturing_allowed': True,
            'created_at': '2020-10-23T10:37:05.085Z', 'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None}
    """

    id: int
    name: str
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    legal_name: str | Unset = UNSET
    address_id: int | None | Unset = UNSET
    address: LocationAddress | None | Unset = UNSET
    is_primary: bool | Unset = UNSET
    sales_allowed: bool | Unset = UNSET
    purchase_allowed: bool | Unset = UNSET
    manufacturing_allowed: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.location_address import LocationAddress

        id = self.id

        name = self.name

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        legal_name = self.legal_name

        address_id: int | None | Unset
        if isinstance(self.address_id, Unset):
            address_id = UNSET
        else:
            address_id = self.address_id

        address: dict[str, Any] | None | Unset
        if isinstance(self.address, Unset):
            address = UNSET
        elif isinstance(self.address, LocationAddress):
            address = self.address.to_dict()
        else:
            address = self.address

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
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        legal_name = d.pop("legal_name", UNSET)

        def _parse_address_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        address_id = _parse_address_id(d.pop("address_id", UNSET))

        def _parse_address(data: object) -> LocationAddress | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                address_type_0 = LocationAddress.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return address_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(LocationAddress | None | Unset, data)

        address = _parse_address(d.pop("address", UNSET))

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
