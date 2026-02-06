from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreatePriceListRequest")


@_attrs_define
class CreatePriceListRequest:
    """Request payload for creating a new price list with market-specific pricing configurations

    Example:
        {'name': 'Premium Customer Pricing'}
    """

    name: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        create_price_list_request = cls(
            name=name,
        )

        return create_price_list_request
