from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.enum_validation_error import EnumValidationError
    from ..models.generic_validation_error import GenericValidationError
    from ..models.invalid_type_validation_error import InvalidTypeValidationError
    from ..models.max_validation_error import MaxValidationError
    from ..models.min_validation_error import MinValidationError
    from ..models.pattern_validation_error import PatternValidationError
    from ..models.required_validation_error import RequiredValidationError
    from ..models.too_big_validation_error import TooBigValidationError
    from ..models.too_small_validation_error import TooSmallValidationError
    from ..models.unrecognized_keys_validation_error import (
        UnrecognizedKeysValidationError,
    )


T = TypeVar("T", bound="DetailedErrorResponse")


@_attrs_define
class DetailedErrorResponse:
    """Enhanced error response containing detailed validation error information for complex request failures"""

    status_code: float | Unset = UNSET
    name: str | Unset = UNSET
    message: str | Unset = UNSET
    code: None | str | Unset = UNSET
    details: (
        list[
            EnumValidationError
            | GenericValidationError
            | InvalidTypeValidationError
            | MaxValidationError
            | MinValidationError
            | PatternValidationError
            | RequiredValidationError
            | TooBigValidationError
            | TooSmallValidationError
            | UnrecognizedKeysValidationError
        ]
        | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.enum_validation_error import EnumValidationError
        from ..models.invalid_type_validation_error import InvalidTypeValidationError
        from ..models.max_validation_error import MaxValidationError
        from ..models.min_validation_error import MinValidationError
        from ..models.pattern_validation_error import PatternValidationError
        from ..models.required_validation_error import RequiredValidationError
        from ..models.too_big_validation_error import TooBigValidationError
        from ..models.too_small_validation_error import TooSmallValidationError
        from ..models.unrecognized_keys_validation_error import (
            UnrecognizedKeysValidationError,
        )

        status_code = self.status_code

        name = self.name

        message = self.message

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        details: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = []
            for details_item_data in self.details:
                details_item: dict[str, Any]
                if isinstance(
                    details_item_data,
                    (
                        EnumValidationError,
                        MinValidationError,
                        MaxValidationError,
                        InvalidTypeValidationError,
                        TooSmallValidationError,
                        TooBigValidationError,
                        RequiredValidationError,
                        PatternValidationError,
                        UnrecognizedKeysValidationError,
                    ),
                ):
                    details_item = details_item_data.to_dict()
                else:
                    details_item = details_item_data.to_dict()

                details.append(details_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status_code is not UNSET:
            field_dict["statusCode"] = status_code
        if name is not UNSET:
            field_dict["name"] = name
        if message is not UNSET:
            field_dict["message"] = message
        if code is not UNSET:
            field_dict["code"] = code
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.enum_validation_error import EnumValidationError
        from ..models.generic_validation_error import GenericValidationError
        from ..models.invalid_type_validation_error import InvalidTypeValidationError
        from ..models.max_validation_error import MaxValidationError
        from ..models.min_validation_error import MinValidationError
        from ..models.pattern_validation_error import PatternValidationError
        from ..models.required_validation_error import RequiredValidationError
        from ..models.too_big_validation_error import TooBigValidationError
        from ..models.too_small_validation_error import TooSmallValidationError
        from ..models.unrecognized_keys_validation_error import (
            UnrecognizedKeysValidationError,
        )

        d = dict(src_dict)
        status_code = d.pop("statusCode", UNSET)

        name = d.pop("name", UNSET)

        message = d.pop("message", UNSET)

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        _details = d.pop("details", UNSET)
        details: (
            list[
                EnumValidationError
                | GenericValidationError
                | InvalidTypeValidationError
                | MaxValidationError
                | MinValidationError
                | PatternValidationError
                | RequiredValidationError
                | TooBigValidationError
                | TooSmallValidationError
                | UnrecognizedKeysValidationError
            ]
            | Unset
        ) = UNSET
        if _details is not UNSET:
            details = []
            for details_item_data in _details:

                def _parse_details_item(
                    data: object,
                ) -> (
                    EnumValidationError
                    | GenericValidationError
                    | InvalidTypeValidationError
                    | MaxValidationError
                    | MinValidationError
                    | PatternValidationError
                    | RequiredValidationError
                    | TooBigValidationError
                    | TooSmallValidationError
                    | UnrecognizedKeysValidationError
                ):
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_0 = (
                            EnumValidationError.from_dict(cast(Mapping[str, Any], data))
                        )

                        return componentsschemas_validation_error_detail_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_1 = (
                            MinValidationError.from_dict(cast(Mapping[str, Any], data))
                        )

                        return componentsschemas_validation_error_detail_type_1
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_2 = (
                            MaxValidationError.from_dict(cast(Mapping[str, Any], data))
                        )

                        return componentsschemas_validation_error_detail_type_2
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_3 = (
                            InvalidTypeValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_3
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_4 = (
                            TooSmallValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_4
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_5 = (
                            TooBigValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_5
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_6 = (
                            RequiredValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_6
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_7 = (
                            PatternValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_7
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_validation_error_detail_type_8 = (
                            UnrecognizedKeysValidationError.from_dict(
                                cast(Mapping[str, Any], data)
                            )
                        )

                        return componentsschemas_validation_error_detail_type_8
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_validation_error_detail_type_9 = (
                        GenericValidationError.from_dict(cast(Mapping[str, Any], data))
                    )

                    return componentsschemas_validation_error_detail_type_9

                details_item = _parse_details_item(details_item_data)

                details.append(details_item)

        detailed_error_response = cls(
            status_code=status_code,
            name=name,
            message=message,
            code=code,
            details=details,
        )

        detailed_error_response.additional_properties = d
        return detailed_error_response

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
