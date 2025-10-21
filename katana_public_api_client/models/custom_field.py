from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CustomField")


@_attrs_define
class CustomField:
    """Individual custom field definition with validation rules and configuration options

    Example:
        {'id': 10, 'name': 'quality_grade', 'field_type': 'select', 'label': 'Quality Grade', 'required': True,
            'options': ['A', 'B', 'C']}
    """

    id: int
    name: str
    field_type: str
    label: str
    required: Unset | bool = UNSET
    options: Unset | list[str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        field_type = self.field_type

        label = self.label

        required = self.required

        options: Unset | list[str] = UNSET
        if not isinstance(self.options, Unset):
            options = self.options

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "field_type": field_type,
                "label": label,
            }
        )
        if required is not UNSET:
            field_dict["required"] = required
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        field_type = d.pop("field_type")

        label = d.pop("label")

        required = d.pop("required", UNSET)

        options = cast(list[str], d.pop("options", UNSET))

        custom_field = cls(
            id=id,
            name=name,
            field_type=field_type,
            label=label,
            required=required,
            options=options,
        )

        custom_field.additional_properties = d
        return custom_field

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
