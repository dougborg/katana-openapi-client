from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_fields_collection_custom_fields_item_field_type import (
    CustomFieldsCollectionCustomFieldsItemFieldType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomFieldsCollectionCustomFieldsItem")


@_attrs_define
class CustomFieldsCollectionCustomFieldsItem:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[Unset, str]):
        field_type (Union[Unset, CustomFieldsCollectionCustomFieldsItemFieldType]):
        required (Union[Unset, bool]):
    """

    id: Union[Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    field_type: Union[Unset, CustomFieldsCollectionCustomFieldsItemFieldType] = UNSET
    required: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        field_type: Union[Unset, str] = UNSET
        if not isinstance(self.field_type, Unset):
            field_type = self.field_type.value

        required = self.required

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if field_type is not UNSET:
            field_dict["field_type"] = field_type
        if required is not UNSET:
            field_dict["required"] = required

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        _field_type = d.pop("field_type", UNSET)
        field_type: Union[Unset, CustomFieldsCollectionCustomFieldsItemFieldType]
        if isinstance(_field_type, Unset):
            field_type = UNSET
        else:
            field_type = CustomFieldsCollectionCustomFieldsItemFieldType(_field_type)

        required = d.pop("required", UNSET)

        custom_fields_collection_custom_fields_item = cls(
            id=id,
            name=name,
            field_type=field_type,
            required=required,
        )

        custom_fields_collection_custom_fields_item.additional_properties = d
        return custom_fields_collection_custom_fields_item

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
