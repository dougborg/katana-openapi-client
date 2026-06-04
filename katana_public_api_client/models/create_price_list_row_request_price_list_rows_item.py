from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.price_list_adjustment_method import PriceListAdjustmentMethod

T = TypeVar("T", bound="CreatePriceListRowRequestPriceListRowsItem")


@_attrs_define
class CreatePriceListRowRequestPriceListRowsItem:
    variant_id: int | Unset = UNSET
    adjustment_method: PriceListAdjustmentMethod | Unset = UNSET
    amount: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        adjustment_method: str | Unset = UNSET
        if not isinstance(self.adjustment_method, Unset):
            adjustment_method = self.adjustment_method.value

        amount = self.amount

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if adjustment_method is not UNSET:
            field_dict["adjustment_method"] = adjustment_method
        if amount is not UNSET:
            field_dict["amount"] = amount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        _adjustment_method = d.pop("adjustment_method", UNSET)
        adjustment_method: PriceListAdjustmentMethod | Unset
        if isinstance(_adjustment_method, Unset):
            adjustment_method = UNSET
        else:
            adjustment_method = PriceListAdjustmentMethod(_adjustment_method)

        amount = d.pop("amount", UNSET)

        create_price_list_row_request_price_list_rows_item = cls(
            variant_id=variant_id,
            adjustment_method=adjustment_method,
            amount=amount,
        )

        create_price_list_row_request_price_list_rows_item.additional_properties = d
        return create_price_list_row_request_price_list_rows_item

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
