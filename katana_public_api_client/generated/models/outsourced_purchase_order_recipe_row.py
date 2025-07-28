import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="OutsourcedPurchaseOrderRecipeRow")


@_attrs_define
class OutsourcedPurchaseOrderRecipeRow:
    id: Unset | int = UNSET
    outsourced_purchase_order_id: Unset | int = UNSET
    bom_row_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    status: Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        outsourced_purchase_order_id = self.outsourced_purchase_order_id

        bom_row_id = self.bom_row_id

        quantity = self.quantity

        status = self.status

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if outsourced_purchase_order_id is not UNSET:
            field_dict["outsourced_purchase_order_id"] = outsourced_purchase_order_id
        if bom_row_id is not UNSET:
            field_dict["bom_row_id"] = bom_row_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        outsourced_purchase_order_id = d.pop("outsourced_purchase_order_id", UNSET)

        bom_row_id = d.pop("bom_row_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        status = d.pop("status", UNSET)

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

        outsourced_purchase_order_recipe_row = cls(
            id=id,
            outsourced_purchase_order_id=outsourced_purchase_order_id,
            bom_row_id=bom_row_id,
            quantity=quantity,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

        outsourced_purchase_order_recipe_row.additional_properties = d
        return outsourced_purchase_order_recipe_row

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
