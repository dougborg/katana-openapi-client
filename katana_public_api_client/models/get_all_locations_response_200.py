from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deletable_entity import DeletableEntity
    from ..models.location_type_0 import LocationType0


T = TypeVar("T", bound="GetAllLocationsResponse200")


@_attrs_define
class GetAllLocationsResponse200:
    data: Unset | list[Union["DeletableEntity", "LocationType0"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.location_type_0 import LocationType0

        data: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item: dict[str, Any]
                if isinstance(data_item_data, LocationType0):
                    data_item = data_item_data.to_dict()
                else:
                    data_item = data_item_data.to_dict()

                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deletable_entity import DeletableEntity
        from ..models.location_type_0 import LocationType0

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:

            def _parse_data_item(
                data: object,
            ) -> Union["DeletableEntity", "LocationType0"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_location_type_0 = LocationType0.from_dict(data)

                    return componentsschemas_location_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_location_type_1 = DeletableEntity.from_dict(data)

                return componentsschemas_location_type_1

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        get_all_locations_response_200 = cls(
            data=data,
        )

        get_all_locations_response_200.additional_properties = d
        return get_all_locations_response_200

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
