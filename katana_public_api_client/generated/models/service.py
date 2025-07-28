from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.service_type import ServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_attributes import ServiceAttributes


T = TypeVar("T", bound="Service")


@_attrs_define
class Service:
    id: Unset | str = UNSET
    type_: Unset | ServiceType = UNSET
    attributes: Union[Unset, "ServiceAttributes"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_: Unset | str = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        attributes: Unset | dict[str, Any] = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if type_ is not UNSET:
            field_dict["type"] = type_
        if attributes is not UNSET:
            field_dict["attributes"] = attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_attributes import ServiceAttributes

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Unset | ServiceType
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ServiceType(_type_)

        _attributes = d.pop("attributes", UNSET)
        attributes: Unset | ServiceAttributes
        if isinstance(_attributes, Unset):
            attributes = UNSET
        else:
            attributes = ServiceAttributes.from_dict(_attributes)

        service = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        service.additional_properties = d
        return service

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
