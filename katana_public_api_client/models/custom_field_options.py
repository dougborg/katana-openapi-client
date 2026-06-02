from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.custom_field_choice import CustomFieldChoice


T = TypeVar("T", bound="CustomFieldOptions")


@_attrs_define
class CustomFieldOptions:
    """Choice configuration for a ``singleSelect`` custom field definition,
    as returned on read and supplied on update.

        Example:
            {'choices': [{'id': 1, 'label': 'Online'}, {'id': 2, 'label': 'Retail'}, {'id': 3, 'label': 'Wholesale'}]}
    """

    choices: list[CustomFieldChoice]

    def to_dict(self) -> dict[str, Any]:
        choices = []
        for choices_item_data in self.choices:
            choices_item = choices_item_data.to_dict()
            choices.append(choices_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "choices": choices,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_choice import CustomFieldChoice

        d = dict(src_dict)
        choices = []
        _choices = d.pop("choices")
        for choices_item_data in _choices:
            choices_item = CustomFieldChoice.from_dict(
                cast(Mapping[str, Any], choices_item_data)
            )

            choices.append(choices_item)

        custom_field_options = cls(
            choices=choices,
        )

        return custom_field_options
