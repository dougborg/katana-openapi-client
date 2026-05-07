from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.additional_properties_validation_error_code import (
    AdditionalPropertiesValidationErrorCode,
)

if TYPE_CHECKING:
    from ..models.additional_properties_validation_error_info import (
        AdditionalPropertiesValidationErrorInfo,
    )


T = TypeVar("T", bound="AdditionalPropertiesValidationError")


@_attrs_define
class AdditionalPropertiesValidationError:
    """Ajv ``additionalProperties`` keyword: an object includes a property
    not permitted by the schema. ``info.additionalProperty`` names the
    offending key.
    """

    path: str
    code: AdditionalPropertiesValidationErrorCode
    message: str
    info: AdditionalPropertiesValidationErrorInfo
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
        from ..models.additional_properties_validation_error_info import (
            AdditionalPropertiesValidationErrorInfo,
        )

        d = dict(src_dict)
        path = d.pop("path")

        code = AdditionalPropertiesValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        info = AdditionalPropertiesValidationErrorInfo.from_dict(d.pop("info"))

        additional_properties_validation_error = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        additional_properties_validation_error.additional_properties = d
        return additional_properties_validation_error

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
