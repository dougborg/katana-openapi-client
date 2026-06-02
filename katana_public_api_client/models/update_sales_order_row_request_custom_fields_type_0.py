from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="UpdateSalesOrderRowRequestCustomFieldsType0")


@_attrs_define
class UpdateSalesOrderRowRequestCustomFieldsType0:
    """Row-level custom field values, keyed by the
    definition ``id`` (UUID) — the ``id`` returned by
    ``GET /custom_field_definitions``, not the field label. Each
    value matches the definition's ``field_type``: string for
    ``shortText`` / ``url``, number for ``number``, boolean for
    ``boolean``, a ``YYYY-MM-DD`` string for ``date``, or the
    integer choice ``id`` for ``singleSelect``.

    On ``PATCH`` the object is **merged** with the existing values,
    not replaced:

    - omit the ``custom_fields`` key — existing values unchanged;
    - ``{"<id>": value}`` — that key is set / overwritten, all
      other keys kept;
    - ``null`` — all custom field values on the row are cleared.

    Keys are tenant-specific, so the schema declares
    ``additionalProperties: true`` rather than enumerating them.

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        update_sales_order_row_request_custom_fields_type_0 = cls()

        update_sales_order_row_request_custom_fields_type_0.additional_properties = d
        return update_sales_order_row_request_custom_fields_type_0

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
