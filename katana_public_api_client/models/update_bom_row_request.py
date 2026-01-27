from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateBomRowRequest")


@_attrs_define
class UpdateBomRowRequest:
    """Request payload for updating an existing BOM row. Only provided fields will be updated.

    Example:
        {'quantity': 3.0, 'notes': 'Updated quantity based on new specifications'}
    """

    ingredient_variant_id: int | Unset = UNSET
    quantity: float | None | Unset = UNSET
    notes: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ingredient_variant_id = self.ingredient_variant_id

        quantity: float | None | Unset
        if isinstance(self.quantity, Unset):
            quantity = UNSET
        else:
            quantity = self.quantity

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ingredient_variant_id is not UNSET:
            field_dict["ingredient_variant_id"] = ingredient_variant_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        ingredient_variant_id = d.pop("ingredient_variant_id", UNSET)

        def _parse_quantity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)  # type: ignore[return-value]

        quantity = _parse_quantity(d.pop("quantity", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)  # type: ignore[return-value]

        notes = _parse_notes(d.pop("notes", UNSET))

        update_bom_row_request = cls(
            ingredient_variant_id=ingredient_variant_id,
            quantity=quantity,
            notes=notes,
        )

        update_bom_row_request.additional_properties = d
        return update_bom_row_request

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
