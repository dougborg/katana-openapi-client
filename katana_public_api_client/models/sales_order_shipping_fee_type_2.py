from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="SalesOrderShippingFeeType2")


@_attrs_define
class SalesOrderShippingFeeType2:
    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        sales_order_shipping_fee_type_2 = cls()

        return sales_order_shipping_fee_type_2
