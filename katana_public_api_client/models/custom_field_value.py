from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CustomFieldValue")


@_attrs_define
class CustomFieldValue:
    """A single custom field value attached to a resource (e.g., a sales
    order, service, product). Custom fields are configured via
    ``GET /custom_fields_collections``; each value pairs the field's
    configured name with the value to set.

        Example:
            {'field_name': 'quality_grade', 'field_value': 'A'}
    """

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

        custom_field_value = cls(
            field_name=field_name,
            field_value=field_value,
        )

        return custom_field_value
