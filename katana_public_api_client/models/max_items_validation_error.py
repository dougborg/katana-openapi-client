from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.max_items_validation_error_code import MaxItemsValidationErrorCode

if TYPE_CHECKING:
    from ..models.max_items_validation_error_info import MaxItemsValidationErrorInfo


T = TypeVar("T", bound="MaxItemsValidationError")


@_attrs_define
class MaxItemsValidationError:
    """Ajv ``maxItems`` keyword: the array exceeds its maximum length."""

    path: str
    code: MaxItemsValidationErrorCode
    message: str
    info: MaxItemsValidationErrorInfo
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        info = self.info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
                "info": info,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.max_items_validation_error_info import MaxItemsValidationErrorInfo

        d = dict(src_dict)
        path = d.pop("path")

        code = MaxItemsValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        info = MaxItemsValidationErrorInfo.from_dict(d.pop("info"))

        max_items_validation_error = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        max_items_validation_error.additional_properties = d
        return max_items_validation_error

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
