from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="MultipleOfValidationErrorInfo")


@_attrs_define
class MultipleOfValidationErrorInfo:
    """Keyword-specific metadata for ``multipleOf``"""

    multiple_of: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        multiple_of = self.multiple_of

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "multipleOf": multiple_of,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        multiple_of = d.pop("multipleOf")

        multiple_of_validation_error_info = cls(
            multiple_of=multiple_of,
        )

        multiple_of_validation_error_info.additional_properties = d
        return multiple_of_validation_error_info

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
