from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.unrecognized_keys_validation_error_code import (
    UnrecognizedKeysValidationErrorCode,
)

T = TypeVar("T", bound="UnrecognizedKeysValidationError")


@_attrs_define
class UnrecognizedKeysValidationError:
    path: str
    code: UnrecognizedKeysValidationErrorCode
    message: str
    keys: list[str]
    valid_keys: Unset | list[str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code.value

        message = self.message

        keys = self.keys

        valid_keys: Unset | list[str] = UNSET
        if not isinstance(self.valid_keys, Unset):
            valid_keys = self.valid_keys

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
                "message": message,
                "keys": keys,
            }
        )
        if valid_keys is not UNSET:
            field_dict["valid_keys"] = valid_keys

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        path = d.pop("path")

        code = UnrecognizedKeysValidationErrorCode(d.pop("code"))

        message = d.pop("message")

        keys = cast(list[str], d.pop("keys"))

        valid_keys = cast(list[str], d.pop("valid_keys", UNSET))

        unrecognized_keys_validation_error = cls(
            path=path,
            code=code,
            message=message,
            keys=keys,
            valid_keys=valid_keys,
        )

        unrecognized_keys_validation_error.additional_properties = d
        return unrecognized_keys_validation_error

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
