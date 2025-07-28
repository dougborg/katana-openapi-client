from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validation_error_detail_info import ValidationErrorDetailInfo


T = TypeVar("T", bound="ValidationErrorDetail")


@_attrs_define
class ValidationErrorDetail:
    """Individual validation error detail"""

    path: str
    code: str
    message: Unset | str = UNSET
    info: Union[Unset, "ValidationErrorDetailInfo"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        code = self.code

        message = self.message

        info: Unset | dict[str, Any] = UNSET
        if not isinstance(self.info, Unset):
            info = self.info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "code": code,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message
        if info is not UNSET:
            field_dict["info"] = info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error_detail_info import ValidationErrorDetailInfo

        d = dict(src_dict)
        path = d.pop("path")

        code = d.pop("code")

        message = d.pop("message", UNSET)

        _info = d.pop("info", UNSET)
        info: Unset | ValidationErrorDetailInfo
        if isinstance(_info, Unset):
            info = UNSET
        else:
            info = ValidationErrorDetailInfo.from_dict(_info)

        validation_error_detail = cls(
            path=path,
            code=code,
            message=message,
            info=info,
        )

        validation_error_detail.additional_properties = d
        return validation_error_detail

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
