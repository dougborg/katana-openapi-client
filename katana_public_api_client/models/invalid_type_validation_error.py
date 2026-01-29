from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.invalid_type_validation_error_code import InvalidTypeValidationErrorCode

T = TypeVar("T", bound="InvalidTypeValidationError")


@_attrs_define
class InvalidTypeValidationError:
    path: str
    code: InvalidTypeValidationErrorCode
    message: str
    expected_type: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        expected_type = self.expected_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
                "expected_type": expected_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        path = d.pop("path")

        code = InvalidTypeValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        expected_type = d.pop("expected_type")

        invalid_type_validation_error = cls(
            path=path,
            code=code,
            message=message,
            expected_type=expected_type,
        )

        invalid_type_validation_error.additional_properties = d
        return invalid_type_validation_error

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
