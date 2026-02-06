from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListRowRequest")


@_attrs_define
class UpdatePriceListRowRequest:
    """Request payload for updating an existing price list row

    Example:
        {'adjustment_method': 'fixed', 'amount': 259.99}
    """

    adjustment_method: str | Unset = UNSET
    amount: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        adjustment_method = self.adjustment_method

        amount = self.amount

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if adjustment_method is not UNSET:
            field_dict["adjustment_method"] = adjustment_method
        if amount is not UNSET:
            field_dict["amount"] = amount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        adjustment_method = d.pop("adjustment_method", UNSET)

        amount = d.pop("amount", UNSET)

        update_price_list_row_request = cls(
            adjustment_method=adjustment_method,
            amount=amount,
        )

        return update_price_list_row_request
