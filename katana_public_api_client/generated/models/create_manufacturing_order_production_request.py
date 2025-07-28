import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

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
    manufacturing_order_id: int
    quantity: float
    production_date: datetime.datetime
    ingredients: Unset | list["ManufacturingOrderProductionIngredient"] = UNSET
    operations: Unset | list["ManufacturingOrderOperationRow"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        quantity = self.quantity

        production_date = self.production_date.isoformat()

        ingredients: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.ingredients, Unset):
            ingredients = []
            for ingredients_item_data in self.ingredients:
                ingredients_item = ingredients_item_data.to_dict()
                ingredients.append(ingredients_item)

        operations: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.operations, Unset):
            operations = []
            for operations_item_data in self.operations:
                operations_item = operations_item_data.to_dict()
                operations.append(operations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "quantity": quantity,
                "production_date": production_date,
            }
        )
        if ingredients is not UNSET:
            field_dict["ingredients"] = ingredients
        if operations is not UNSET:
            field_dict["operations"] = operations

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

        quantity = d.pop("quantity")

        production_date = isoparse(d.pop("production_date"))

        ingredients = []
        _ingredients = d.pop("ingredients", UNSET)
        for ingredients_item_data in _ingredients or []:
            ingredients_item = ManufacturingOrderProductionIngredient.from_dict(
                ingredients_item_data
            )

            ingredients.append(ingredients_item)

        operations = []
        _operations = d.pop("operations", UNSET)
        for operations_item_data in _operations or []:
            operations_item = ManufacturingOrderOperationRow.from_dict(
                operations_item_data
            )

            operations.append(operations_item)

        create_manufacturing_order_production_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            quantity=quantity,
            production_date=production_date,
            ingredients=ingredients,
            operations=operations,
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
