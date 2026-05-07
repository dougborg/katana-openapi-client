from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.min_length_validation_error_code import MinLengthValidationErrorCode

if TYPE_CHECKING:
    from ..models.min_length_validation_error_info import MinLengthValidationErrorInfo


T = TypeVar("T", bound="MinLengthValidationError")


@_attrs_define
class MinLengthValidationError:
    """Ajv ``minLength`` keyword: the string is shorter than the schema's
    minimum length. Parallel to ``MaxLengthValidationError`` — the limit
    lives in ``info.limit``.
    """

    path: str
    code: MinLengthValidationErrorCode
    message: str
    info: MinLengthValidationErrorInfo
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
        from ..models.min_length_validation_error_info import (
            MinLengthValidationErrorInfo,
        )

        d = dict(src_dict)
        path = d.pop("path")

        code = MinLengthValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        info = MinLengthValidationErrorInfo.from_dict(d.pop("info"))

        min_length_validation_error = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        min_length_validation_error.additional_properties = d
        return min_length_validation_error

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
