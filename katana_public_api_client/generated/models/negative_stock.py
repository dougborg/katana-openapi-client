import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="NegativeStock")


@_attrs_define
class NegativeStock:
    variant_id: Unset | int = UNSET
    location_id: Unset | int = UNSET
    latest_negative_stock_date: Unset | datetime.datetime = UNSET
    name: Unset | str = UNSET
    sku: Unset | str = UNSET
    category: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        latest_negative_stock_date: Unset | str = UNSET
        if not isinstance(self.latest_negative_stock_date, Unset):
            latest_negative_stock_date = self.latest_negative_stock_date.isoformat()

        name = self.name

        sku = self.sku

        category = self.category

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if latest_negative_stock_date is not UNSET:
            field_dict["latest_negative_stock_date"] = latest_negative_stock_date
        if name is not UNSET:
            field_dict["name"] = name
        if sku is not UNSET:
            field_dict["sku"] = sku
        if category is not UNSET:
            field_dict["category"] = category

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        _latest_negative_stock_date = d.pop("latest_negative_stock_date", UNSET)
        latest_negative_stock_date: Unset | datetime.datetime
        if isinstance(_latest_negative_stock_date, Unset):
            latest_negative_stock_date = UNSET
        else:
            latest_negative_stock_date = isoparse(_latest_negative_stock_date)

        name = d.pop("name", UNSET)

        sku = d.pop("sku", UNSET)

        category = d.pop("category", UNSET)

        negative_stock = cls(
            variant_id=variant_id,
            location_id=location_id,
            latest_negative_stock_date=latest_negative_stock_date,
            name=name,
            sku=sku,
            category=category,
        )

        negative_stock.additional_properties = d
        return negative_stock

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
