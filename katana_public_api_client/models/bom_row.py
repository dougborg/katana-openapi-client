import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="BomRow")


@_attrs_define
class BomRow:
    """Bill of Materials row defining ingredient requirements for product manufacturing

    Example:
        {'id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'product_variant_id': 2001, 'product_item_id': 3001,
            'ingredient_variant_id': 2002, 'quantity': 2.5, 'notes': 'Handle with care - fragile component', 'created_at':
            '2023-10-15T14:30:00Z', 'updated_at': '2023-10-16T09:15:00Z'}

    Attributes:
        id (UUID): Unique UUID identifier for the BOM row
        product_variant_id (int): ID of the product variant this BOM row belongs to
        product_item_id (int): ID of the product item this BOM row belongs to
        ingredient_variant_id (int): ID of the ingredient variant used in this BOM row
        quantity (Union[None, Unset, float]): Required quantity of the ingredient variant
        notes (Union[None, Unset, str]): Additional notes for this BOM row
        created_at (Union[Unset, datetime.datetime]): Timestamp when the BOM row was created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the BOM row was last updated
    """

    id: UUID
    product_variant_id: int
    product_item_id: int
    ingredient_variant_id: int
    quantity: None | Unset | float = UNSET
    notes: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        product_variant_id = self.product_variant_id

        product_item_id = self.product_item_id

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

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "product_variant_id": product_variant_id,
                "product_item_id": product_item_id,
                "ingredient_variant_id": ingredient_variant_id,
            }
        )
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if notes is not UNSET:
            field_dict["notes"] = notes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        product_variant_id = d.pop("product_variant_id")

        product_item_id = d.pop("product_item_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

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

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        bom_row = cls(
            id=id,
            product_variant_id=product_variant_id,
            product_item_id=product_item_id,
            ingredient_variant_id=ingredient_variant_id,
            quantity=quantity,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )

        bom_row.additional_properties = d
        return bom_row

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
