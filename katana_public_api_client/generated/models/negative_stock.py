import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

T = TypeVar("T", bound="NegativeStock")


@_attrs_define
class NegativeStock:
    id: int
    variant_id: int
    location_id: int
    latest_negative_stock_date: datetime.datetime
    name: str
    sku: str
    category: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        variant_id = self.variant_id

        location_id = self.location_id

        latest_negative_stock_date = self.latest_negative_stock_date.isoformat()

        name = self.name

        sku = self.sku

        category = self.category

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "variant_id": variant_id,
                "location_id": location_id,
                "latest_negative_stock_date": latest_negative_stock_date,
                "name": name,
                "sku": sku,
                "category": category,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        latest_negative_stock_date = isoparse(d.pop("latest_negative_stock_date"))

        name = d.pop("name")

        sku = d.pop("sku")

        category = d.pop("category")

        negative_stock = cls(
            id=id,
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
