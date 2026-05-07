from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="OneOfValidationErrorInfo")


@_attrs_define
class OneOfValidationErrorInfo:
    """Keyword-specific metadata for ``oneOf``"""

    passing_schemas: list[int] | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        passing_schemas: list[int] | None
        if isinstance(self.passing_schemas, list):
            passing_schemas = self.passing_schemas

        else:
            passing_schemas = self.passing_schemas

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "passingSchemas": passing_schemas,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_passing_schemas(data: object) -> list[int] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                passing_schemas_type_0 = cast(list[int], data)

                return passing_schemas_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | None, data)

        passing_schemas = _parse_passing_schemas(d.pop("passingSchemas"))

        one_of_validation_error_info = cls(
            passing_schemas=passing_schemas,
        )

        one_of_validation_error_info.additional_properties = d
        return one_of_validation_error_info

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
