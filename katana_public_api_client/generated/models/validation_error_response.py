from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validation_error_detail import ValidationErrorDetail


T = TypeVar("T", bound="ValidationErrorResponse")


@_attrs_define
class ValidationErrorResponse:
    status_code: float
    name: str
    message: str
    code: None | Unset | str = UNSET
    details: Unset | list["ValidationErrorDetail"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status_code = self.status_code

        name = self.name

        message = self.message

        code: None | Unset | str
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        details: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.details, Unset):
            details = []
            for details_item_data in self.details:
                details_item = details_item_data.to_dict()
                details.append(details_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "statusCode": status_code,
                "name": name,
                "message": message,
            }
        )
        if code is not UNSET:
            field_dict["code"] = code
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error_detail import ValidationErrorDetail

        d = dict(src_dict)
        status_code = d.pop("statusCode")

        name = d.pop("name")

        message = d.pop("message")

        def _parse_code(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        code = _parse_code(d.pop("code", UNSET))

        details = []
        _details = d.pop("details", UNSET)
        for details_item_data in _details or []:
            details_item = ValidationErrorDetail.from_dict(details_item_data)

            details.append(details_item)

        validation_error_response = cls(
            status_code=status_code,
            name=name,
            message=message,
            code=code,
            details=details,
        )

        validation_error_response.additional_properties = d
        return validation_error_response

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
