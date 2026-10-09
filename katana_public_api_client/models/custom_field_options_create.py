from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.custom_field_options_create_appears_on_item import (
    CustomFieldOptionsCreateAppearsOnItem,
)

if TYPE_CHECKING:
    from ..models.custom_field_choice_create import CustomFieldChoiceCreate


T = TypeVar("T", bound="CustomFieldOptionsCreate")


@_attrs_define
class CustomFieldOptionsCreate:
    """Extra configuration for the definition. `choices` is only meaningful when `field_type` is `singleSelect`;
    `appearsOn` is only meaningful on a variant definition. Omit (or send `null`) when neither applies.

        Example:
            {'choices': [{'label': 'Online'}, {'label': 'Retail'}, {'label': 'Wholesale'}]}
    """

    choices: list[CustomFieldChoiceCreate] | Unset = UNSET
    appears_on: list[CustomFieldOptionsCreateAppearsOnItem] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        choices: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = []
            for choices_item_data in self.choices:
                choices_item = choices_item_data.to_dict()
                choices.append(choices_item)

        appears_on: list[str] | Unset = UNSET
        if not isinstance(self.appears_on, Unset):
            appears_on = []
            for appears_on_item_data in self.appears_on:
                appears_on_item = appears_on_item_data.value
                appears_on.append(appears_on_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if choices is not UNSET:
            field_dict["choices"] = choices
        if appears_on is not UNSET:
            field_dict["appearsOn"] = appears_on

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_choice_create import (
            CustomFieldChoiceCreate,
        )

        d = dict(src_dict)
        _choices = d.pop("choices", UNSET)
        choices: list[CustomFieldChoiceCreate] | Unset = UNSET
        if _choices is not UNSET:
            choices = []
            for choices_item_data in _choices:
                choices_item = CustomFieldChoiceCreate.from_dict(
                    cast(Mapping[str, Any], choices_item_data)
                )

                choices.append(choices_item)

        _appears_on = d.pop("appearsOn", UNSET)
        appears_on: list[CustomFieldOptionsCreateAppearsOnItem] | Unset = UNSET
        if _appears_on is not UNSET:
            appears_on = []
            for appears_on_item_data in _appears_on:
                appears_on_item = CustomFieldOptionsCreateAppearsOnItem(
                    appears_on_item_data
                )

                appears_on.append(appears_on_item)

        custom_field_options_create = cls(
            choices=choices,
            appears_on=appears_on,
        )

        return custom_field_options_create
