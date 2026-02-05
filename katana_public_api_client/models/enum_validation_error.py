from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.enum_validation_error_code import EnumValidationErrorCode

T = TypeVar("T", bound="EnumValidationError")


@_attrs_define
class EnumValidationError:
    path: str
    code: EnumValidationErrorCode
    message: str
    allowed_values: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        allowed_values = self.allowed_values

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
                "allowed_values": allowed_values,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        code = EnumValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        allowed_values = cast(list[str], d.pop("allowed_values"))

        enum_validation_error = cls(
            path=path,
            code=code,
            message=message,
            allowed_values=allowed_values,
        )

        enum_validation_error.additional_properties = d
        return enum_validation_error

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
