from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CustomFieldValue")


@_attrs_define
class CustomFieldValue:
    """A single custom field value in the **legacy** ``{field_name,
    field_value}`` shape used by Variant / Product / Material / Service
    resources. These fields are configured via the
    ``/custom_fields_collections`` surface and attached as an **array**
    of name/value pairs.

    This is distinct from — and must not be unified with — the newer
    sales-order custom-fields surface, where ``custom_fields`` is a
    **dict keyed by custom field definition ``id`` (UUID)** registered
    through ``/custom_field_definitions`` (see ``CustomFieldDefinition``
    and the ``custom_fields`` property on ``SalesOrder`` /
    ``SalesOrderRow``). The two surfaces coexist. Variant and service
    update requests also accept the UUID-keyed map when that feature
    is enabled for the account; this schema describes the legacy item.

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
