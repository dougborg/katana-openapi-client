from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.exclusive_maximum_validation_error_code import (
    ExclusiveMaximumValidationErrorCode,
)

if TYPE_CHECKING:
    from ..models.exclusive_maximum_validation_error_info import (
        ExclusiveMaximumValidationErrorInfo,
    )


T = TypeVar("T", bound="ExclusiveMaximumValidationError")


@_attrs_define
class ExclusiveMaximumValidationError:
    """Ajv ``exclusiveMaximum`` keyword: the value must be strictly less than
    ``info.limit``.
    """

    path: str
    code: ExclusiveMaximumValidationErrorCode
    message: str
    info: ExclusiveMaximumValidationErrorInfo
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
        from ..models.exclusive_maximum_validation_error_info import (
            ExclusiveMaximumValidationErrorInfo,
        )

        d = dict(src_dict)
        path = d.pop("path")

        code = ExclusiveMaximumValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        info = ExclusiveMaximumValidationErrorInfo.from_dict(d.pop("info"))

        exclusive_maximum_validation_error = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        exclusive_maximum_validation_error.additional_properties = d
        return exclusive_maximum_validation_error

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
