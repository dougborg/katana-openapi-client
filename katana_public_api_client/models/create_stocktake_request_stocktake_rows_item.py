from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateStocktakeRequestStocktakeRowsItem")


@_attrs_define
class CreateStocktakeRequestStocktakeRowsItem:
    variant_id: int | Unset = UNSET
    batch_id: int | Unset = UNSET
    counted_quantity: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        batch_id = self.batch_id

        counted_quantity = self.counted_quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        batch_id = d.pop("batch_id", UNSET)

        counted_quantity = d.pop("counted_quantity", UNSET)

        create_stocktake_request_stocktake_rows_item = cls(
            variant_id=variant_id,
            batch_id=batch_id,
            counted_quantity=counted_quantity,
        )

        create_stocktake_request_stocktake_rows_item.additional_properties = d
        return create_stocktake_request_stocktake_rows_item

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
