from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location_address import LocationAddress


T = TypeVar("T", bound="LocationType0")


@_attrs_define
class LocationType0:
    """
    Attributes:
        id (int):
        name (str):
        legal_name (Union[Unset, str]):
        address_id (Union[Unset, int]):
        address (Union[Unset, LocationAddress]): Physical address information for manufacturing locations and warehouse
            facilities Example: {'id': 5001, 'city': 'Austin', 'country': 'US', 'line_1': '1500 Industrial Blvd', 'line_2':
            'Building A', 'state': 'TX', 'zip': '78745'}.
        is_primary (Union[Unset, bool]):
        sales_allowed (Union[Unset, bool]):
        purchase_allowed (Union[Unset, bool]):
        manufacturing_allowed (Union[Unset, bool]):
    """

    id: int
    name: str
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

        location_type_0 = cls(
            id=id,
            name=name,
            legal_name=legal_name,
            address_id=address_id,
            address=address,
            is_primary=is_primary,
            sales_allowed=sales_allowed,
            purchase_allowed=purchase_allowed,
            manufacturing_allowed=manufacturing_allowed,
        )

        location_type_0.additional_properties = d
        return location_type_0

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
