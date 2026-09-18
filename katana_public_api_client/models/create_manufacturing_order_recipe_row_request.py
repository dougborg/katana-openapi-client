from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
        CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
    )
    from ..models.manufacturing_order_ingredient_traceability_request import (
        ManufacturingOrderIngredientTraceabilityRequest,
    )


T = TypeVar("T", bound="CreateManufacturingOrderRecipeRowRequest")


@_attrs_define
class CreateManufacturingOrderRecipeRowRequest:
    """Request payload for creating a new manufacturing order recipe row to track ingredient requirements and consumption

    Example:
        {'manufacturing_order_id': 1001, 'variant_id': 2002, 'notes': 'Use fresh ingredients from cold storage',
            'planned_quantity_per_unit': 0.25, 'total_actual_quantity': 5.0, 'batch_transactions': [{'batch_id': 301,
            'quantity': 3.0}, {'batch_id': 302, 'quantity': 2.0}]}
    """

    manufacturing_order_id: int
    variant_id: int
    planned_quantity_per_unit: float
    notes: str | Unset = UNSET
    total_actual_quantity: float | Unset = UNSET
    batch_transactions: (
        list[CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
    ) = UNSET
    traceability: list[ManufacturingOrderIngredientTraceabilityRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        variant_id = self.variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

        notes = self.notes

        total_actual_quantity = self.total_actual_quantity

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        traceability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.traceability, Unset):
            traceability = []
            for traceability_item_data in self.traceability:
                traceability_item = traceability_item_data.to_dict()
                traceability.append(traceability_item)

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
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if traceability is not UNSET:
            field_dict["traceability"] = traceability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_manufacturing_order_recipe_row_request_batch_transactions_item import (
            CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
        )
        from ..models.manufacturing_order_ingredient_traceability_request import (
            ManufacturingOrderIngredientTraceabilityRequest,
        )

        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        variant_id = d.pop("variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

        notes = d.pop("notes", UNSET)

        total_actual_quantity = d.pop("total_actual_quantity", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: (
            list[CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem] | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem.from_dict(
                    cast(Mapping[str, Any], batch_transactions_item_data)
                )

                batch_transactions.append(batch_transactions_item)

        _traceability = d.pop("traceability", UNSET)
        traceability: list[ManufacturingOrderIngredientTraceabilityRequest] | Unset = (
            UNSET
        )
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = (
                    ManufacturingOrderIngredientTraceabilityRequest.from_dict(
                        cast(Mapping[str, Any], traceability_item_data)
                    )
                )

                traceability.append(traceability_item)

        create_manufacturing_order_recipe_row_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            variant_id=variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            total_actual_quantity=total_actual_quantity,
            batch_transactions=batch_transactions,
            traceability=traceability,
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
