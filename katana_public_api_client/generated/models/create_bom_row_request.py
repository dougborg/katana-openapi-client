from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateBomRowRequest")


@_attrs_define
class CreateBomRowRequest:
    product_variant_id: int
    ingredient_variant_id: int
    quantity: float
    notes: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        product_variant_id = self.product_variant_id

        ingredient_variant_id = self.ingredient_variant_id

        quantity = self.quantity

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "product_variant_id": product_variant_id,
                "ingredient_variant_id": ingredient_variant_id,
                "quantity": quantity,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        product_variant_id = d.pop("product_variant_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        quantity = d.pop("quantity")

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        create_bom_row_request = cls(
            product_variant_id=product_variant_id,
            ingredient_variant_id=ingredient_variant_id,
            quantity=quantity,
            notes=notes,
        )

        create_bom_row_request.additional_properties = d
        return create_bom_row_request

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
