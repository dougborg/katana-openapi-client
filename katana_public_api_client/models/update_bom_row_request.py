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

    ingredient_variant_id: Unset | int = UNSET
    quantity: None | Unset | float = UNSET
    notes: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ingredient_variant_id = self.ingredient_variant_id

        quantity: None | Unset | float
        if isinstance(self.quantity, Unset):
            quantity = UNSET
        else:
            quantity = self.quantity

        notes: None | Unset | str
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ingredient_variant_id = d.pop("ingredient_variant_id", UNSET)

        def _parse_quantity(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity = _parse_quantity(d.pop("quantity", UNSET))

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

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
