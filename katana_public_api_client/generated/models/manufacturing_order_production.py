import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_operation_production import (
        ManufacturingOrderOperationProduction,
    )
    from ..models.manufacturing_order_production_ingredient import (
        ManufacturingOrderProductionIngredient,
    )
    from ..models.serial_number import SerialNumber


T = TypeVar("T", bound="ManufacturingOrderProduction")


@_attrs_define
class ManufacturingOrderProduction:
    id: Unset | int = UNSET
    manufacturing_order_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    production_date: Unset | datetime.datetime = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    ingredients: Unset | list["ManufacturingOrderProductionIngredient"] = UNSET
    operations: Unset | list["ManufacturingOrderOperationProduction"] = UNSET
    serial_numbers: Unset | list["SerialNumber"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        manufacturing_order_id = self.manufacturing_order_id

        quantity = self.quantity

        production_date: Unset | str = UNSET
        if not isinstance(self.production_date, Unset):
            production_date = self.production_date.isoformat()

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
        if manufacturing_order_id is not UNSET:
            field_dict["manufacturing_order_id"] = manufacturing_order_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if production_date is not UNSET:
            field_dict["production_date"] = production_date
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if ingredients is not UNSET:
            field_dict["ingredients"] = ingredients
        if operations is not UNSET:
            field_dict["operations"] = operations
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manufacturing_order_operation_production import (
            ManufacturingOrderOperationProduction,
        )
        from ..models.manufacturing_order_production_ingredient import (
            ManufacturingOrderProductionIngredient,
        )
        from ..models.serial_number import SerialNumber

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        manufacturing_order_id = d.pop("manufacturing_order_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        _production_date = d.pop("production_date", UNSET)
        production_date: Unset | datetime.datetime
        if isinstance(_production_date, Unset):
            production_date = UNSET
        else:
            production_date = isoparse(_production_date)

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
            operations_item = ManufacturingOrderOperationProduction.from_dict(
                operations_item_data
            )

            operations.append(operations_item)

        serial_numbers = []
        _serial_numbers = d.pop("serial_numbers", UNSET)
        for serial_numbers_item_data in _serial_numbers or []:
            serial_numbers_item = SerialNumber.from_dict(serial_numbers_item_data)

            serial_numbers.append(serial_numbers_item)

        manufacturing_order_production = cls(
            id=id,
            manufacturing_order_id=manufacturing_order_id,
            quantity=quantity,
            production_date=production_date,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            ingredients=ingredients,
            operations=operations,
            serial_numbers=serial_numbers,
        )

        manufacturing_order_production.additional_properties = d
        return manufacturing_order_production

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
