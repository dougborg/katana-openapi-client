from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.minimum_validation_error_code import MinimumValidationErrorCode

if TYPE_CHECKING:
    from ..models.minimum_validation_error_info import MinimumValidationErrorInfo


T = TypeVar("T", bound="MinimumValidationError")


@_attrs_define
class MinimumValidationError:
    """Ajv ``minimum`` keyword: the value is below its inclusive lower bound."""

    path: str
    code: MinimumValidationErrorCode
    message: str
    info: MinimumValidationErrorInfo
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
        from ..models.minimum_validation_error_info import MinimumValidationErrorInfo

        d = dict(src_dict)
        path = d.pop("path")

        code = MinimumValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        info = MinimumValidationErrorInfo.from_dict(d.pop("info"))

        minimum_validation_error = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        minimum_validation_error.additional_properties = d
        return minimum_validation_error

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
