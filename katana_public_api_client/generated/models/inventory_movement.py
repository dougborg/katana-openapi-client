import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.inventory_movement_resource_type import InventoryMovementResourceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="InventoryMovement")


@_attrs_define
class InventoryMovement:
    """Details of a single inventory movement record."""

    id: int
    variant_id: int
    location_id: int
    resource_type: InventoryMovementResourceType
    movement_date: datetime.datetime
    quantity_change: float
    balance_after: float
    value_per_unit: float
    value_in_stock_after: float
    average_cost_after: float
    created_at: datetime.datetime
    updated_at: datetime.datetime
    resource_id: Unset | int = UNSET
    caused_by_order_no: Unset | str = UNSET
    caused_by_resource_id: Unset | int = UNSET
    rank: Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        variant_id = self.variant_id

        location_id = self.location_id

        resource_type = self.resource_type.value

        movement_date = self.movement_date.isoformat()

        quantity_change = self.quantity_change

        balance_after = self.balance_after

        value_per_unit = self.value_per_unit

        value_in_stock_after = self.value_in_stock_after

        average_cost_after = self.average_cost_after

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        resource_id = self.resource_id

        caused_by_order_no = self.caused_by_order_no

        caused_by_resource_id = self.caused_by_resource_id

        rank = self.rank

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "variant_id": variant_id,
                "location_id": location_id,
                "resource_type": resource_type,
                "movement_date": movement_date,
                "quantity_change": quantity_change,
                "balance_after": balance_after,
                "value_per_unit": value_per_unit,
                "value_in_stock_after": value_in_stock_after,
                "average_cost_after": average_cost_after,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if resource_id is not UNSET:
            field_dict["resource_id"] = resource_id
        if caused_by_order_no is not UNSET:
            field_dict["caused_by_order_no"] = caused_by_order_no
        if caused_by_resource_id is not UNSET:
            field_dict["caused_by_resource_id"] = caused_by_resource_id
        if rank is not UNSET:
            field_dict["rank"] = rank

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        resource_type = InventoryMovementResourceType(d.pop("resource_type"))

        movement_date = isoparse(d.pop("movement_date"))

        quantity_change = d.pop("quantity_change")

        balance_after = d.pop("balance_after")

        value_per_unit = d.pop("value_per_unit")

        value_in_stock_after = d.pop("value_in_stock_after")

        average_cost_after = d.pop("average_cost_after")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        resource_id = d.pop("resource_id", UNSET)

        caused_by_order_no = d.pop("caused_by_order_no", UNSET)

        caused_by_resource_id = d.pop("caused_by_resource_id", UNSET)

        rank = d.pop("rank", UNSET)

        inventory_movement = cls(
            id=id,
            variant_id=variant_id,
            location_id=location_id,
            resource_type=resource_type,
            movement_date=movement_date,
            quantity_change=quantity_change,
            balance_after=balance_after,
            value_per_unit=value_per_unit,
            value_in_stock_after=value_in_stock_after,
            average_cost_after=average_cost_after,
            created_at=created_at,
            updated_at=updated_at,
            resource_id=resource_id,
            caused_by_order_no=caused_by_order_no,
            caused_by_resource_id=caused_by_resource_id,
            rank=rank,
        )

        inventory_movement.additional_properties = d
        return inventory_movement

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
