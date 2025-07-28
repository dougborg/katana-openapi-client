from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.service_request_data_type import ServiceRequestDataType

if TYPE_CHECKING:
    from ..models.service_input_attributes import ServiceInputAttributes


T = TypeVar("T", bound="ServiceRequestData")


@_attrs_define
class ServiceRequestData:
    type_: ServiceRequestDataType
    attributes: "ServiceInputAttributes"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_input_attributes import ServiceInputAttributes

        d = dict(src_dict)
        type_ = ServiceRequestDataType(d.pop("type"))

        attributes = ServiceInputAttributes.from_dict(d.pop("attributes"))

        service_request_data = cls(
            type_=type_,
            attributes=attributes,
        )

        service_request_data.additional_properties = d
        return service_request_data

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
