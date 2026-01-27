from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.too_big_validation_error_code import TooBigValidationErrorCode

T = TypeVar("T", bound="TooBigValidationError")


@_attrs_define
class TooBigValidationError:
    path: str
    code: TooBigValidationErrorCode
    message: str
    max_length: int | Unset = UNSET
    max_items: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        max_length = self.max_length

        max_items = self.max_items

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
            }
        )
        if max_length is not UNSET:
            field_dict["max_length"] = max_length
        if max_items is not UNSET:
            field_dict["max_items"] = max_items

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        path = d.pop("path")

        code = TooBigValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        max_length = d.pop("max_length", UNSET)

        max_items = d.pop("max_items", UNSET)

        too_big_validation_error = cls(
            path=path,
            code=code,
            message=message,
            max_length=max_length,
            max_items=max_items,
        )

        too_big_validation_error.additional_properties = d
        return too_big_validation_error

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
