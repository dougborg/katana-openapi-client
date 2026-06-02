from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CustomFieldChoiceCreate")


@_attrs_define
class CustomFieldChoiceCreate:
    """A single ``singleSelect`` choice as supplied on
    ``POST /custom_field_definitions``. Send only the ``label`` — the
    server assigns the integer ``id`` and returns it in the response.

        Example:
            {'label': 'Online'}
    """

    label: str

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "label": label,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label = d.pop("label")

        custom_field_choice_create = cls(
            label=label,
        )

        return custom_field_choice_create
