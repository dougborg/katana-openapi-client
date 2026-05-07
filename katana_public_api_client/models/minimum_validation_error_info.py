from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.minimum_validation_error_info_comparison import (
    MinimumValidationErrorInfoComparison,
)

T = TypeVar("T", bound="MinimumValidationErrorInfo")


@_attrs_define
class MinimumValidationErrorInfo:
    """Keyword-specific metadata for ``minimum``"""

    limit: float
    comparison: MinimumValidationErrorInfoComparison | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limit = self.limit

        comparison: str | Unset = UNSET
        if not isinstance(self.comparison, Unset):
            comparison = self.comparison.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limit": limit,
            }
        )
        if comparison is not UNSET:
            field_dict["comparison"] = comparison

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        limit = d.pop("limit")

        _comparison = d.pop("comparison", UNSET)
        comparison: MinimumValidationErrorInfoComparison | Unset
        if isinstance(_comparison, Unset):
            comparison = UNSET
        else:
            comparison = MinimumValidationErrorInfoComparison(_comparison)

        minimum_validation_error_info = cls(
            limit=limit,
            comparison=comparison,
        )

        minimum_validation_error_info.additional_properties = d
        return minimum_validation_error_info

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
