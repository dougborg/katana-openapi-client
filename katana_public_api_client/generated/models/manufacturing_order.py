import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.manufacturing_order_status import ManufacturingOrderStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.serial_number import SerialNumber


T = TypeVar("T", bound="ManufacturingOrder")


@_attrs_define
class ManufacturingOrder:
    id: Unset | int = UNSET
    status: Unset | ManufacturingOrderStatus = UNSET
    order_no: Unset | str = UNSET
    variant_id: Unset | int = UNSET
    planned_quantity: Unset | float = UNSET
    actual_quantity: None | Unset | float = UNSET
    location_id: Unset | int = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    production_deadline_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    is_linked_to_sales_order: Unset | bool = UNSET
    ingredient_availability: Unset | str = UNSET
    total_cost: Unset | float = UNSET
    total_actual_time: Unset | float = UNSET
    total_planned_time: Unset | float = UNSET
    sales_order_id: Unset | int = UNSET
    sales_order_row_id: Unset | int = UNSET
    sales_order_delivery_deadline: Unset | datetime.datetime = UNSET
    material_cost: Unset | float = UNSET
    subassemblies_cost: Unset | float = UNSET
    operations_cost: Unset | float = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    serial_numbers: Unset | list["SerialNumber"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        order_no = self.order_no

        variant_id = self.variant_id

        planned_quantity = self.planned_quantity

        actual_quantity: None | Unset | float
        if isinstance(self.actual_quantity, Unset):
            actual_quantity = UNSET
        else:
            actual_quantity = self.actual_quantity

        location_id = self.location_id

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        production_deadline_date: Unset | str = UNSET
        if not isinstance(self.production_deadline_date, Unset):
            production_deadline_date = self.production_deadline_date.isoformat()

        additional_info = self.additional_info

        is_linked_to_sales_order = self.is_linked_to_sales_order

        ingredient_availability = self.ingredient_availability

        total_cost = self.total_cost

        total_actual_time = self.total_actual_time

        total_planned_time = self.total_planned_time

        sales_order_id = self.sales_order_id

        sales_order_row_id = self.sales_order_row_id

        sales_order_delivery_deadline: Unset | str = UNSET
        if not isinstance(self.sales_order_delivery_deadline, Unset):
            sales_order_delivery_deadline = (
                self.sales_order_delivery_deadline.isoformat()
            )

        material_cost = self.material_cost

        subassemblies_cost = self.subassemblies_cost

        operations_cost = self.operations_cost

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        serial_numbers: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.serial_numbers, Unset):
            serial_numbers = []
            for serial_numbers_item_data in self.serial_numbers:
                serial_numbers_item = serial_numbers_item_data.to_dict()
                serial_numbers.append(serial_numbers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if planned_quantity is not UNSET:
            field_dict["planned_quantity"] = planned_quantity
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if is_linked_to_sales_order is not UNSET:
            field_dict["is_linked_to_sales_order"] = is_linked_to_sales_order
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if total_cost is not UNSET:
            field_dict["total_cost"] = total_cost
        if total_actual_time is not UNSET:
            field_dict["total_actual_time"] = total_actual_time
        if total_planned_time is not UNSET:
            field_dict["total_planned_time"] = total_planned_time
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if sales_order_row_id is not UNSET:
            field_dict["sales_order_row_id"] = sales_order_row_id
        if sales_order_delivery_deadline is not UNSET:
            field_dict["sales_order_delivery_deadline"] = sales_order_delivery_deadline
        if material_cost is not UNSET:
            field_dict["material_cost"] = material_cost
        if subassemblies_cost is not UNSET:
            field_dict["subassemblies_cost"] = subassemblies_cost
        if operations_cost is not UNSET:
            field_dict["operations_cost"] = operations_cost
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.serial_number import SerialNumber

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | ManufacturingOrderStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ManufacturingOrderStatus(_status)

        order_no = d.pop("order_no", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        planned_quantity = d.pop("planned_quantity", UNSET)

        def _parse_actual_quantity(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        actual_quantity = _parse_actual_quantity(d.pop("actual_quantity", UNSET))

        location_id = d.pop("location_id", UNSET)

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

        is_linked_to_sales_order = d.pop("is_linked_to_sales_order", UNSET)

        ingredient_availability = d.pop("ingredient_availability", UNSET)

        total_cost = d.pop("total_cost", UNSET)

        total_actual_time = d.pop("total_actual_time", UNSET)

        total_planned_time = d.pop("total_planned_time", UNSET)

        sales_order_id = d.pop("sales_order_id", UNSET)

        sales_order_row_id = d.pop("sales_order_row_id", UNSET)

        _sales_order_delivery_deadline = d.pop("sales_order_delivery_deadline", UNSET)
        sales_order_delivery_deadline: Unset | datetime.datetime
        if isinstance(_sales_order_delivery_deadline, Unset):
            sales_order_delivery_deadline = UNSET
        else:
            sales_order_delivery_deadline = isoparse(_sales_order_delivery_deadline)

        material_cost = d.pop("material_cost", UNSET)

        subassemblies_cost = d.pop("subassemblies_cost", UNSET)

        operations_cost = d.pop("operations_cost", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        serial_numbers = []
        _serial_numbers = d.pop("serial_numbers", UNSET)
        for serial_numbers_item_data in _serial_numbers or []:
            serial_numbers_item = SerialNumber.from_dict(serial_numbers_item_data)

            serial_numbers.append(serial_numbers_item)

        manufacturing_order = cls(
            id=id,
            status=status,
            order_no=order_no,
            variant_id=variant_id,
            planned_quantity=planned_quantity,
            actual_quantity=actual_quantity,
            location_id=location_id,
            order_created_date=order_created_date,
            production_deadline_date=production_deadline_date,
            additional_info=additional_info,
            is_linked_to_sales_order=is_linked_to_sales_order,
            ingredient_availability=ingredient_availability,
            total_cost=total_cost,
            total_actual_time=total_actual_time,
            total_planned_time=total_planned_time,
            sales_order_id=sales_order_id,
            sales_order_row_id=sales_order_row_id,
            sales_order_delivery_deadline=sales_order_delivery_deadline,
            material_cost=material_cost,
            subassemblies_cost=subassemblies_cost,
            operations_cost=operations_cost,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            serial_numbers=serial_numbers,
        )

        manufacturing_order.additional_properties = d
        return manufacturing_order

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
