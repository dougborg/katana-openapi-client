from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_transaction_request import BatchTransactionRequest
    from ..models.create_outsourced_purchase_order_recipe_row_request_custom_fields_type_0 import (
        CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="CreateOutsourcedPurchaseOrderRecipeRowRequest")


@_attrs_define
class CreateOutsourcedPurchaseOrderRecipeRowRequest:
    """Request payload for creating a new outsourced purchase order recipe row"""

    purchase_order_row_id: int
    ingredient_variant_id: int
    planned_quantity_per_unit: float
    notes: str | Unset = UNSET
    batch_transactions: list[BatchTransactionRequest] | Unset = UNSET
    custom_fields: (
        CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0 | Unset | None
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_outsourced_purchase_order_recipe_row_request_custom_fields_type_0 import (
            CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0,
        )

        purchase_order_row_id = self.purchase_order_row_id

        ingredient_variant_id = self.ingredient_variant_id

        planned_quantity_per_unit = self.planned_quantity_per_unit

        notes = self.notes

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields,
            CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0,
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "purchase_order_row_id": purchase_order_row_id,
                "ingredient_variant_id": ingredient_variant_id,
                "planned_quantity_per_unit": planned_quantity_per_unit,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction_request import (
            BatchTransactionRequest,
        )
        from ..models.create_outsourced_purchase_order_recipe_row_request_custom_fields_type_0 import (
            CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0,
        )

        d = dict(src_dict)
        purchase_order_row_id = d.pop("purchase_order_row_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        planned_quantity_per_unit = d.pop("planned_quantity_per_unit")

        notes = d.pop("notes", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransactionRequest] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransactionRequest.from_dict(
                    cast(Mapping[str, Any], batch_transactions_item_data)
                )

                batch_transactions.append(batch_transactions_item)

        def _parse_custom_fields(
            data: object,
        ) -> (
            CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0
            | Unset
            | None
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                CreateOutsourcedPurchaseOrderRecipeRowRequestCustomFieldsType0
                | Unset
                | None,
                data,
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        create_outsourced_purchase_order_recipe_row_request = cls(
            purchase_order_row_id=purchase_order_row_id,
            ingredient_variant_id=ingredient_variant_id,
            planned_quantity_per_unit=planned_quantity_per_unit,
            notes=notes,
            batch_transactions=batch_transactions,
            custom_fields=custom_fields,
        )

        return create_outsourced_purchase_order_recipe_row_request
