from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.price_adjustment_method import PriceAdjustmentMethod

T = TypeVar("T", bound="UpdatePriceListRowRequest")


@_attrs_define
class UpdatePriceListRowRequest:
    """Request payload for updating an existing price list row

    Example:
        {'variant_id': 67890, 'adjustment_method': 'fixed', 'amount': 259.99}
    """

    variant_id: int | Unset = UNSET
    adjustment_method: PriceAdjustmentMethod | Unset = UNSET
    amount: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        adjustment_method: str | Unset = UNSET
        if not isinstance(self.adjustment_method, Unset):
            adjustment_method = self.adjustment_method.value

        amount = self.amount

        field_dict: dict[str, Any] = {}

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
        adjustment_method: PriceAdjustmentMethod | Unset
        if isinstance(_adjustment_method, Unset):
            adjustment_method = UNSET
        else:
            adjustment_method = PriceAdjustmentMethod(_adjustment_method)

        amount = d.pop("amount", UNSET)

        update_price_list_row_request = cls(
            variant_id=variant_id,
            adjustment_method=adjustment_method,
            amount=amount,
        )

        return update_price_list_row_request
