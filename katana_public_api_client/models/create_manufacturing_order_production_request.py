from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_operation_row import (
        ManufacturingOrderOperationRow,
    )
    from ..models.manufacturing_order_production_ingredient import (
        ManufacturingOrderProductionIngredient,
    )


T = TypeVar("T", bound="CreateManufacturingOrderProductionRequest")


@_attrs_define
class CreateManufacturingOrderProductionRequest:
    """Request payload for creating a production run within a manufacturing order, recording actual production activities
    and material consumption.

        Example:
            {'manufacturing_order_id': 3001, 'completed_quantity': 25, 'completed_date': '2024-01-20T14:30:00Z', 'is_final':
                False, 'ingredients': [{'id': 4001, 'location_id': 1, 'variant_id': 3101, 'manufacturing_order_id': 3001,
                'manufacturing_order_recipe_row_id': 3201, 'production_id': 3501, 'quantity': 50.0, 'production_date':
                '2024-01-20T14:30:00Z', 'cost': 125.0}], 'operations': [{'id': 3801, 'manufacturing_order_id': 3001,
                'operation_id': 401, 'time': 15.0}]}
    """

    manufacturing_order_id: int
    completed_quantity: float
    completed_date: datetime.datetime
    is_final: bool | Unset = UNSET
    ingredients: list[ManufacturingOrderProductionIngredient] | Unset = UNSET
    operations: list[ManufacturingOrderOperationRow] | Unset = UNSET
    serial_numbers: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        completed_quantity = self.completed_quantity

        completed_date = self.completed_date.isoformat()

        is_final = self.is_final

        ingredients: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.ingredients, Unset):
            ingredients = []
            for ingredients_item_data in self.ingredients:
                ingredients_item = ingredients_item_data.to_dict()
                ingredients.append(ingredients_item)

        operations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.operations, Unset):
            operations = []
            for operations_item_data in self.operations:
                operations_item = operations_item_data.to_dict()
                operations.append(operations_item)

        serial_numbers: list[str] | Unset = UNSET
        if not isinstance(self.serial_numbers, Unset):
            serial_numbers = self.serial_numbers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "completed_quantity": completed_quantity,
                "completed_date": completed_date,
            }
        )
        if is_final is not UNSET:
            field_dict["is_final"] = is_final
        if ingredients is not UNSET:
            field_dict["ingredients"] = ingredients
        if operations is not UNSET:
            field_dict["operations"] = operations
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manufacturing_order_operation_row import (
            ManufacturingOrderOperationRow,
        )
        from ..models.manufacturing_order_production_ingredient import (
            ManufacturingOrderProductionIngredient,
        )

        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        completed_quantity = d.pop("completed_quantity")

        completed_date = isoparse(d.pop("completed_date"))

        is_final = d.pop("is_final", UNSET)

        _ingredients = d.pop("ingredients", UNSET)
        ingredients: list[ManufacturingOrderProductionIngredient] | Unset = UNSET
        if _ingredients is not UNSET:
            ingredients = []
            for ingredients_item_data in _ingredients:
                ingredients_item = ManufacturingOrderProductionIngredient.from_dict(
                    ingredients_item_data
                )

                ingredients.append(ingredients_item)

        _operations = d.pop("operations", UNSET)
        operations: list[ManufacturingOrderOperationRow] | Unset = UNSET
        if _operations is not UNSET:
            operations = []
            for operations_item_data in _operations:
                operations_item = ManufacturingOrderOperationRow.from_dict(
                    operations_item_data
                )

                operations.append(operations_item)

        serial_numbers = cast(list[str], d.pop("serial_numbers", UNSET))

        create_manufacturing_order_production_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            completed_quantity=completed_quantity,
            completed_date=completed_date,
            is_final=is_final,
            ingredients=ingredients,
            operations=operations,
            serial_numbers=serial_numbers,
        )

        create_manufacturing_order_production_request.additional_properties = d
        return create_manufacturing_order_production_request

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
