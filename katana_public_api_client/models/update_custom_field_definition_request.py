from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_custom_field_definition_request_options_type_0 import (
        UpdateCustomFieldDefinitionRequestOptionsType0,
    )


T = TypeVar("T", bound="UpdateCustomFieldDefinitionRequest")


@_attrs_define
class UpdateCustomFieldDefinitionRequest:
    """Request payload for updating an existing custom field definition.

    Example:
        {'label': 'Quality Grade (revised)', 'description': 'Updated customer-facing quality classification'}
    """

    label: str | Unset = UNSET
    description: None | str | Unset = UNSET
    options: None | Unset | UpdateCustomFieldDefinitionRequestOptionsType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_custom_field_definition_request_options_type_0 import (
            UpdateCustomFieldDefinitionRequestOptionsType0,
        )

        label = self.label

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, UpdateCustomFieldDefinitionRequestOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if label is not UNSET:
            field_dict["label"] = label
        if description is not UNSET:
            field_dict["description"] = description
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_custom_field_definition_request_options_type_0 import (
            UpdateCustomFieldDefinitionRequestOptionsType0,
        )

        d = dict(src_dict)
        label = d.pop("label", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_options(
            data: object,
        ) -> None | Unset | UpdateCustomFieldDefinitionRequestOptionsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = (
                    UpdateCustomFieldDefinitionRequestOptionsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                None | Unset | UpdateCustomFieldDefinitionRequestOptionsType0, data
            )

        options = _parse_options(d.pop("options", UNSET))

        update_custom_field_definition_request = cls(
            label=label,
            description=description,
            options=options,
        )

        return update_custom_field_definition_request
