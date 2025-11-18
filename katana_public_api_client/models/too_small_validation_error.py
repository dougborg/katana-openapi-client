from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.too_small_validation_error_code import TooSmallValidationErrorCode

T = TypeVar("T", bound="TooSmallValidationError")


@_attrs_define
class TooSmallValidationError:
    path: str
    code: TooSmallValidationErrorCode
    message: str
    min_length: Unset | int = UNSET
    min_items: Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        min_length = self.min_length

        min_items = self.min_items

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
            }
        )
        if min_length is not UNSET:
            field_dict["min_length"] = min_length
        if min_items is not UNSET:
            field_dict["min_items"] = min_items

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        path = d.pop("path")

        code = TooSmallValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        min_length = d.pop("min_length", UNSET)

        min_items = d.pop("min_items", UNSET)

        too_small_validation_error = cls(
            path=path,
            code=code,
            message=message,
            min_length=min_length,
            min_items=min_items,
        )

        too_small_validation_error.additional_properties = d
        return too_small_validation_error

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
