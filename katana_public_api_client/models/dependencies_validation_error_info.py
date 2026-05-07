from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="DependenciesValidationErrorInfo")


@_attrs_define
class DependenciesValidationErrorInfo:
    """Keyword-specific metadata for ``dependencies``"""

    property_: str
    missing_property: str
    deps: str | Unset = UNSET
    deps_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        property_ = self.property_

        missing_property = self.missing_property

        deps = self.deps

        deps_count = self.deps_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "property": property_,
                "missingProperty": missing_property,
            }
        )
        if deps is not UNSET:
            field_dict["deps"] = deps
        if deps_count is not UNSET:
            field_dict["depsCount"] = deps_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        property_ = d.pop("property")

        missing_property = d.pop("missingProperty")

        deps = d.pop("deps", UNSET)

        deps_count = d.pop("depsCount", UNSET)

        dependencies_validation_error_info = cls(
            property_=property_,
            missing_property=missing_property,
            deps=deps,
            deps_count=deps_count,
        )

        dependencies_validation_error_info.additional_properties = d
        return dependencies_validation_error_info

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
