from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="CreateSalesOrderRequestCustomFieldsType0")


@_attrs_define
class CreateSalesOrderRequestCustomFieldsType0:
    """Custom field values for the sales order, keyed by configured
    field name. Keys correspond to fields defined for the
    ``SalesOrder`` entity type on the tenant's
    ``custom_field_collection`` (see
    ``GET /custom_fields_collections``). Each value matches the
    corresponding field's ``CustomFieldType`` (``shortText`` /
    ``number`` / ``singleSelect`` / ``date`` / ``boolean`` /
    ``url``). The valid key set is tenant-specific runtime
    config, so the schema declares ``additionalProperties: true``
    rather than enumerating keys.

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        create_sales_order_request_custom_fields_type_0 = cls()

        create_sales_order_request_custom_fields_type_0.additional_properties = d
        return create_sales_order_request_custom_fields_type_0

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
