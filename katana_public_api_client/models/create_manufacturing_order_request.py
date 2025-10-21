import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateManufacturingOrderRequest")


@_attrs_define
class CreateManufacturingOrderRequest:
    """Request payload for creating a new manufacturing order to initiate production of products or components.

    Example:
        {'variant_id': 2101, 'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for new product launch'}

    Attributes:
        variant_id (int): ID of the product variant to manufacture
        planned_quantity (float): Quantity of the variant to produce
        location_id (int): ID of the factory location where production will take place
        order_created_date (Union[Unset, datetime.datetime]): Date and time when the manufacturing order should be
            created (defaults to current time)
        production_deadline_date (Union[Unset, datetime.datetime]): Target deadline for completing production
        additional_info (Union[Unset, str]): Optional notes or additional information about the order
    """

    variant_id: int
    planned_quantity: float
    location_id: int
    order_created_date: Unset | datetime.datetime = UNSET
    production_deadline_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        planned_quantity = self.planned_quantity

        location_id = self.location_id

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        production_deadline_date: Unset | str = UNSET
        if not isinstance(self.production_deadline_date, Unset):
            production_deadline_date = self.production_deadline_date.isoformat()

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "planned_quantity": planned_quantity,
                "location_id": location_id,
            }
        )
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        planned_quantity = d.pop("planned_quantity")

        location_id = d.pop("location_id")

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        _production_deadline_date = d.pop("production_deadline_date", UNSET)
        production_deadline_date: Unset | datetime.datetime
        if isinstance(_production_deadline_date, Unset):
            production_deadline_date = UNSET
        else:
            production_deadline_date = isoparse(_production_deadline_date)

        additional_info = d.pop("additional_info", UNSET)

        create_manufacturing_order_request = cls(
            variant_id=variant_id,
            planned_quantity=planned_quantity,
            location_id=location_id,
            order_created_date=order_created_date,
            production_deadline_date=production_deadline_date,
            additional_info=additional_info,
        )

        create_manufacturing_order_request.additional_properties = d
        return create_manufacturing_order_request

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
