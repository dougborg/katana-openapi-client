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
    from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
        CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
    )


T = TypeVar("T", bound="CreateManufacturingOrderRecipeRowRequest")


@_attrs_define
class CreateManufacturingOrderRecipeRowRequest:
    manufacturing_order_id: int
    variant_id: int
    planned_quantity_per_unit: float
    notes: Unset | str = UNSET
    total_actual_quantity: Unset | float = UNSET
    ingredient_availability: Unset | str = UNSET
    ingredient_expected_date: Unset | datetime.datetime = UNSET
    batch_transactions: (
        Unset | list["CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem"]
    ) = UNSET
    cost: Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        variant_id = self.variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

        notes = self.notes

        total_actual_quantity = self.total_actual_quantity

        ingredient_availability = self.ingredient_availability

        ingredient_expected_date: Unset | str = UNSET
        if not isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        cost = self.cost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "variant_id": variant_id,
                "planned_quantity_per_unit": planned_quantity_per_unit,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if total_actual_quantity is not UNSET:
            field_dict["total_actual_quantity"] = total_actual_quantity
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if cost is not UNSET:
            field_dict["cost"] = cost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
            CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
        )

        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        variant_id = d.pop("variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

        notes = d.pop("notes", UNSET)

        total_actual_quantity = d.pop("total_actual_quantity", UNSET)

        ingredient_availability = d.pop("ingredient_availability", UNSET)

        _ingredient_expected_date = d.pop("ingredient_expected_date", UNSET)
        ingredient_expected_date: Unset | datetime.datetime
        if isinstance(_ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        else:
            ingredient_expected_date = isoparse(_ingredient_expected_date)

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = (
                CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )
            )

            batch_transactions.append(batch_transactions_item)

        cost = d.pop("cost", UNSET)

        create_manufacturing_order_recipe_row_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            variant_id=variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            total_actual_quantity=total_actual_quantity,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            batch_transactions=batch_transactions,
            cost=cost,
        )

        create_manufacturing_order_recipe_row_request.additional_properties = d
        return create_manufacturing_order_recipe_row_request

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
