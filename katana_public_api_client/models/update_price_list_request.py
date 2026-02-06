from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListRequest")


@_attrs_define
class UpdatePriceListRequest:
    """Request payload for updating an existing price list

    Example:
        {'name': 'Premium Customer Pricing - Updated', 'is_active': True}
    """

    name: str | Unset = UNSET
    is_active: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        is_active = self.is_active

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        is_active = d.pop("is_active", UNSET)

        update_price_list_request = cls(
            name=name,
            is_active=is_active,
        )

        return update_price_list_request
