from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.manufacturing_order_status import ManufacturingOrderStatus

if TYPE_CHECKING:
    from ..models.batch_transaction import BatchTransaction
    from ..models.manufacturing_order_traceability_request import (
        ManufacturingOrderTraceabilityRequest,
    )
    from ..models.update_manufacturing_order_request_custom_fields_type_0 import (
        UpdateManufacturingOrderRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdateManufacturingOrderRequest")


@_attrs_define
class UpdateManufacturingOrderRequest:
    """Request payload for updating an existing manufacturing order's properties and production parameters.

    Example:
        {'planned_quantity': 75, 'additional_info': 'Increased quantity due to additional customer demand',
            'production_deadline_date': '2024-01-30T17:00:00Z'}
    """

    custom_fields: Unset | UpdateManufacturingOrderRequestCustomFieldsType0 | None = (
        UNSET
    )
    status: ManufacturingOrderStatus | Unset = UNSET
    order_no: str | Unset = UNSET
    variant_id: int | Unset = UNSET
    location_id: int | Unset = UNSET
    planned_quantity: float | Unset = UNSET
    actual_quantity: float | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    production_deadline_date: datetime.datetime | Unset = UNSET
    done_date: datetime.datetime | Unset = UNSET
    additional_info: str | Unset = UNSET
    batch_transactions: list[BatchTransaction] | Unset = UNSET
    traceability: list[ManufacturingOrderTraceabilityRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_manufacturing_order_request_custom_fields_type_0 import (
            UpdateManufacturingOrderRequestCustomFieldsType0,
        )

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, UpdateManufacturingOrderRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        order_no = self.order_no

        variant_id = self.variant_id

        location_id = self.location_id

        planned_quantity = self.planned_quantity

        actual_quantity = self.actual_quantity

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        production_deadline_date: str | Unset = UNSET
        if not isinstance(self.production_deadline_date, Unset):
            production_deadline_date = self.production_deadline_date.isoformat()

        done_date: str | Unset = UNSET
        if not isinstance(self.done_date, Unset):
            done_date = self.done_date.isoformat()

        additional_info = self.additional_info

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
        field_dict.update({})
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
        if status is not UNSET:
            field_dict["status"] = status
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if planned_quantity is not UNSET:
            field_dict["planned_quantity"] = planned_quantity
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date
        if done_date is not UNSET:
            field_dict["done_date"] = done_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if traceability is not UNSET:
            field_dict["traceability"] = traceability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction import BatchTransaction
        from ..models.manufacturing_order_traceability_request import (
            ManufacturingOrderTraceabilityRequest,
        )
        from ..models.update_manufacturing_order_request_custom_fields_type_0 import (
            UpdateManufacturingOrderRequestCustomFieldsType0,
        )

        d = dict(src_dict)

        def _parse_custom_fields(
            data: object,
        ) -> Unset | UpdateManufacturingOrderRequestCustomFieldsType0 | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    UpdateManufacturingOrderRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                Unset | UpdateManufacturingOrderRequestCustomFieldsType0 | None, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        _status = d.pop("status", UNSET)
        status: ManufacturingOrderStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ManufacturingOrderStatus(_status)

        order_no = d.pop("order_no", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        planned_quantity = d.pop("planned_quantity", UNSET)

        actual_quantity = d.pop("actual_quantity", UNSET)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: datetime.datetime | Unset
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = datetime.datetime.fromisoformat(_order_created_date)

        _production_deadline_date = d.pop("production_deadline_date", UNSET)
        production_deadline_date: datetime.datetime | Unset
        if isinstance(_production_deadline_date, Unset):
            production_deadline_date = UNSET
        else:
            production_deadline_date = datetime.datetime.fromisoformat(
                _production_deadline_date
            )

        _done_date = d.pop("done_date", UNSET)
        done_date: datetime.datetime | Unset
        if isinstance(_done_date, Unset):
            done_date = UNSET
        else:
            done_date = datetime.datetime.fromisoformat(_done_date)

        additional_info = d.pop("additional_info", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransaction] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransaction.from_dict(
                    cast(Mapping[str, Any], batch_transactions_item_data)
                )

                batch_transactions.append(batch_transactions_item)

        _traceability = d.pop("traceability", UNSET)
        traceability: list[ManufacturingOrderTraceabilityRequest] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = ManufacturingOrderTraceabilityRequest.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        update_manufacturing_order_request = cls(
            custom_fields=custom_fields,
            status=status,
            order_no=order_no,
            variant_id=variant_id,
            location_id=location_id,
            planned_quantity=planned_quantity,
            actual_quantity=actual_quantity,
            order_created_date=order_created_date,
            production_deadline_date=production_deadline_date,
            done_date=done_date,
            additional_info=additional_info,
            batch_transactions=batch_transactions,
            traceability=traceability,
        )

        update_manufacturing_order_request.additional_properties = d
        return update_manufacturing_order_request

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
