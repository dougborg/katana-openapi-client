import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.outsourced_purchase_order_recipe_row_ingredient_availability import (
    OutsourcedPurchaseOrderRecipeRowIngredientAvailability,
)

if TYPE_CHECKING:
    from ..models.outsourced_purchase_order_recipe_row_batch_transactions_item import (
        OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="OutsourcedPurchaseOrderRecipeRow")


@_attrs_define
class OutsourcedPurchaseOrderRecipeRow:
    """Recipe ingredient row for outsourced purchase orders defining material requirements and availability"""

    id: int
    purchase_order_row_id: int
    ingredient_variant_id: int
    planned_quantity_per_unit: float
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    purchase_order_id: Unset | int = UNSET
    ingredient_availability: (
        Unset | OutsourcedPurchaseOrderRecipeRowIngredientAvailability
    ) = UNSET
    ingredient_expected_date: None | Unset | datetime.datetime = UNSET
    notes: None | Unset | str = UNSET
    batch_transactions: (
        Unset | list["OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem"]
    ) = UNSET
    cost: None | Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        purchase_order_row_id = self.purchase_order_row_id

        ingredient_variant_id = self.ingredient_variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

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

        purchase_order_id = self.purchase_order_id

        ingredient_availability: Unset | str = UNSET
        if not isinstance(self.ingredient_availability, Unset):
            ingredient_availability = self.ingredient_availability.value

        ingredient_expected_date: None | Unset | str
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        elif isinstance(self.ingredient_expected_date, datetime.datetime):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()
        else:
            ingredient_expected_date = self.ingredient_expected_date

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        cost: None | Unset | float
        if isinstance(self.cost, Unset):
            cost = UNSET
        else:
            cost = self.cost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "purchase_order_row_id": purchase_order_row_id,
                "ingredient_variant_id": ingredient_variant_id,
                "planned_quantity_per_unit": planned_quantity_per_unit,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if purchase_order_id is not UNSET:
            field_dict["purchase_order_id"] = purchase_order_id
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date
        if notes is not UNSET:
            field_dict["notes"] = notes
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if cost is not UNSET:
            field_dict["cost"] = cost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.outsourced_purchase_order_recipe_row_batch_transactions_item import (
            OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        purchase_order_row_id = d.pop("purchase_order_row_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

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

        purchase_order_id = d.pop("purchase_order_id", UNSET)

        _ingredient_availability = d.pop("ingredient_availability", UNSET)
        ingredient_availability: (
            Unset | OutsourcedPurchaseOrderRecipeRowIngredientAvailability
        )
        if isinstance(_ingredient_availability, Unset):
            ingredient_availability = UNSET
        else:
            ingredient_availability = (
                OutsourcedPurchaseOrderRecipeRowIngredientAvailability(
                    _ingredient_availability
                )
            )

        def _parse_ingredient_expected_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_expected_date_type_0 = isoparse(data)

                return ingredient_expected_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        ingredient_expected_date = _parse_ingredient_expected_date(
            d.pop("ingredient_expected_date", UNSET)
        )

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = (
                OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )
            )

            batch_transactions.append(batch_transactions_item)

        def _parse_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        cost = _parse_cost(d.pop("cost", UNSET))

        outsourced_purchase_order_recipe_row = cls(
            id=id,
            purchase_order_row_id=purchase_order_row_id,
            ingredient_variant_id=ingredient_variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            purchase_order_id=purchase_order_id,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            notes=notes,
            batch_transactions=batch_transactions,
            cost=cost,
        )

        outsourced_purchase_order_recipe_row.additional_properties = d
        return outsourced_purchase_order_recipe_row

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
