from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateVariantRequestConfigAttributesItem")


@_attrs_define
class CreateVariantRequestConfigAttributesItem:
    config_name: str
    config_value: str

    def to_dict(self) -> dict[str, Any]:
        config_name = self.config_name

        config_value = self.config_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "config_name": config_name,
                "config_value": config_value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        config_name = d.pop("config_name")

        config_value = d.pop("config_value")

        create_variant_request_config_attributes_item = cls(
            config_name=config_name,
            config_value=config_value,
        )

        return create_variant_request_config_attributes_item
