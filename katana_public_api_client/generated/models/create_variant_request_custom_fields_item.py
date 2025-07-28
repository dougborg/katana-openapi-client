from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateVariantRequestCustomFieldsItem")


@_attrs_define
class CreateVariantRequestCustomFieldsItem:
    field_name: str
    field_value: str

    def to_dict(self) -> dict[str, Any]:
        field_name = self.field_name

        field_value = self.field_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "field_name": field_name,
                "field_value": field_value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field_name = d.pop("field_name")

        field_value = d.pop("field_value")

        create_variant_request_custom_fields_item = cls(
            field_name=field_name,
            field_value=field_value,
        )

        return create_variant_request_custom_fields_item
