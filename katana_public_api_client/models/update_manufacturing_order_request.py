from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_manufacturing_order_request_status import (
    UpdateManufacturingOrderRequestStatus,
)

if TYPE_CHECKING:
    from ..models.batch_transaction import BatchTransaction


T = TypeVar("T", bound="UpdateManufacturingOrderRequest")


@_attrs_define
class UpdateManufacturingOrderRequest:
    """Request payload for updating an existing manufacturing order's properties and production parameters.

    Example:
        {'planned_quantity': 75, 'additional_info': 'Increased quantity due to additional customer demand',
            'production_deadline_date': '2024-01-30T17:00:00Z'}
    """

    status: UpdateManufacturingOrderRequestStatus | Unset = UNSET
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
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction import BatchTransaction

        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: UpdateManufacturingOrderRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateManufacturingOrderRequestStatus(_status)

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
            order_created_date = isoparse(_order_created_date)

        _production_deadline_date = d.pop("production_deadline_date", UNSET)
        production_deadline_date: datetime.datetime | Unset
        if isinstance(_production_deadline_date, Unset):
            production_deadline_date = UNSET
        else:
            production_deadline_date = isoparse(_production_deadline_date)

        _done_date = d.pop("done_date", UNSET)
        done_date: datetime.datetime | Unset
        if isinstance(_done_date, Unset):
            done_date = UNSET
        else:
            done_date = isoparse(_done_date)

        additional_info = d.pop("additional_info", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[BatchTransaction] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = BatchTransaction.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        update_manufacturing_order_request = cls(
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
