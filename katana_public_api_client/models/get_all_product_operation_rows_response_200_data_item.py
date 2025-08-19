from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="GetAllProductOperationRowsResponse200DataItem")


@_attrs_define
class GetAllProductOperationRowsResponse200DataItem:
    id: Unset | int = UNSET
    product_id: Unset | int = UNSET
    operation_id: Unset | int = UNSET
    sequence: Unset | int = UNSET
    notes: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        product_id = self.product_id

        operation_id = self.operation_id

        sequence = self.sequence

        notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if operation_id is not UNSET:
            field_dict["operation_id"] = operation_id
        if sequence is not UNSET:
            field_dict["sequence"] = sequence
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        product_id = d.pop("product_id", UNSET)

        operation_id = d.pop("operation_id", UNSET)

        sequence = d.pop("sequence", UNSET)

        notes = d.pop("notes", UNSET)

        get_all_product_operation_rows_response_200_data_item = cls(
            id=id,
            product_id=product_id,
            operation_id=operation_id,
            sequence=sequence,
            notes=notes,
        )

        get_all_product_operation_rows_response_200_data_item.additional_properties = d
        return get_all_product_operation_rows_response_200_data_item

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
