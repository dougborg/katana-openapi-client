from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_transaction import BatchTransaction
    from ..models.traceability_request import TraceabilityRequest
    from ..models.update_sales_order_row_request_attributes_item import (
        UpdateSalesOrderRowRequestAttributesItem,
    )
    from ..models.update_sales_order_row_request_custom_fields_type_0 import (
        UpdateSalesOrderRowRequestCustomFieldsType0,
    )
    from ..models.update_sales_order_row_request_serial_number_transactions_item import (
        UpdateSalesOrderRowRequestSerialNumberTransactionsItem,
    )


T = TypeVar("T", bound="UpdateSalesOrderRowRequest")


@_attrs_define
class UpdateSalesOrderRowRequest:
    """Request payload for updating an existing sales order row

    Example:
        {'quantity': 3, 'price_per_unit': 549.99}
    """

    variant_id: int | Unset = UNSET
    quantity: float | Unset = UNSET
    price_per_unit: float | Unset = UNSET
    tax_rate_id: int | Unset = UNSET
    location_id: int | Unset = UNSET
    total_discount: float | Unset = UNSET
    batch_transactions: list[BatchTransaction] | Unset = UNSET
    serial_number_transactions: (
        list[UpdateSalesOrderRowRequestSerialNumberTransactionsItem] | Unset
    ) = UNSET
    traceability: list[TraceabilityRequest] | Unset = UNSET
    attributes: list[UpdateSalesOrderRowRequestAttributesItem] | Unset = UNSET
    custom_fields: None | Unset | UpdateSalesOrderRowRequestCustomFieldsType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_sales_order_row_request_custom_fields_type_0 import (
            UpdateSalesOrderRowRequestCustomFieldsType0,
        )

        variant_id = self.variant_id

        quantity = self.quantity

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        location_id = self.location_id

        total_discount = self.total_discount

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        serial_number_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.serial_number_transactions, Unset):
            serial_number_transactions = []
            for serial_number_transactions_item_data in self.serial_number_transactions:
                serial_number_transactions_item = (
                    serial_number_transactions_item_data.to_dict()
                )
                serial_number_transactions.append(serial_number_transactions_item)

        traceability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.traceability, Unset):
            traceability = []
            for traceability_item_data in self.traceability:
                traceability_item = traceability_item_data.to_dict()
                traceability.append(traceability_item)

        attributes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        custom_fields: dict[str, Any] | None | Unset
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, UpdateSalesOrderRowRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if total_discount is not UNSET:
            field_dict["total_discount"] = total_discount
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if serial_number_transactions is not UNSET:
            field_dict["serial_number_transactions"] = serial_number_transactions
        if traceability is not UNSET:
            field_dict["traceability"] = traceability
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction import BatchTransaction
        from ..models.traceability_request import TraceabilityRequest
        from ..models.update_sales_order_row_request_attributes_item import (
            UpdateSalesOrderRowRequestAttributesItem,
        )
        from ..models.update_sales_order_row_request_custom_fields_type_0 import (
            UpdateSalesOrderRowRequestCustomFieldsType0,
        )
        from ..models.update_sales_order_row_request_serial_number_transactions_item import (
            UpdateSalesOrderRowRequestSerialNumberTransactionsItem,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        price_per_unit = d.pop("price_per_unit", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        total_discount = d.pop("total_discount", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransaction] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransaction.from_dict(
                    cast(Mapping[str, Any], batch_transactions_item_data)
                )

                batch_transactions.append(batch_transactions_item)

        _serial_number_transactions = d.pop("serial_number_transactions", UNSET)
        serial_number_transactions: (
            list[UpdateSalesOrderRowRequestSerialNumberTransactionsItem] | Unset
        ) = UNSET
        if _serial_number_transactions is not UNSET:
            serial_number_transactions = []
            for serial_number_transactions_item_data in _serial_number_transactions:
                serial_number_transactions_item = (
                    UpdateSalesOrderRowRequestSerialNumberTransactionsItem.from_dict(
                        cast(Mapping[str, Any], serial_number_transactions_item_data)
                    )
                )

                serial_number_transactions.append(serial_number_transactions_item)

        _traceability = d.pop("traceability", UNSET)
        traceability: list[TraceabilityRequest] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = TraceabilityRequest.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        _attributes = d.pop("attributes", UNSET)
        attributes: list[UpdateSalesOrderRowRequestAttributesItem] | Unset = UNSET
        if _attributes is not UNSET:
            attributes = []
            for attributes_item_data in _attributes:
                attributes_item = UpdateSalesOrderRowRequestAttributesItem.from_dict(
                    cast(Mapping[str, Any], attributes_item_data)
                )

                attributes.append(attributes_item)

        def _parse_custom_fields(
            data: object,
        ) -> None | Unset | UpdateSalesOrderRowRequestCustomFieldsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    UpdateSalesOrderRowRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                None | Unset | UpdateSalesOrderRowRequestCustomFieldsType0, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        update_sales_order_row_request = cls(
            variant_id=variant_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
            total_discount=total_discount,
            batch_transactions=batch_transactions,
            serial_number_transactions=serial_number_transactions,
            traceability=traceability,
            attributes=attributes,
            custom_fields=custom_fields,
        )

        return update_sales_order_row_request
