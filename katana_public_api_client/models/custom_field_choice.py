from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CustomFieldChoice")


@_attrs_define
class CustomFieldChoice:
    """A single ``singleSelect`` choice as it appears on read and update.
    The integer ``id`` is what gets stored on the entity; ``label`` is
    the human-readable text resolved client-side.

        Example:
            {'id': 1, 'label': 'Online'}
    """

    label: str
    id: int | Unset = UNSET
    deleted: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        id = self.id

        deleted = self.deleted

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "label": label,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if deleted is not UNSET:
            field_dict["deleted"] = deleted

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label = d.pop("label")

        id = d.pop("id", UNSET)

        deleted = d.pop("deleted", UNSET)

        custom_field_choice = cls(
            label=label,
            id=id,
            deleted=deleted,
        )

        return custom_field_choice
