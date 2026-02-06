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
from ..models.create_manufacturing_order_request_status import (
    CreateManufacturingOrderRequestStatus,
)

if TYPE_CHECKING:
    from ..models.batch_transaction import BatchTransaction


T = TypeVar("T", bound="CreateManufacturingOrderRequest")


@_attrs_define
class CreateManufacturingOrderRequest:
    """Request payload for creating a new manufacturing order to initiate production of products or components.

    Example:
        {'variant_id': 2101, 'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for new product launch'}
    """

    variant_id: int
    location_id: int
    planned_quantity: float
    status: CreateManufacturingOrderRequestStatus | Unset = UNSET
    order_no: str | Unset = UNSET
    actual_quantity: float | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    production_deadline_date: datetime.datetime | Unset = UNSET
    additional_info: str | Unset = UNSET
    batch_transactions: list[BatchTransaction] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        planned_quantity = self.planned_quantity

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        order_no = self.order_no

        actual_quantity = self.actual_quantity

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        production_deadline_date: str | Unset = UNSET
        if not isinstance(self.production_deadline_date, Unset):
            production_deadline_date = self.production_deadline_date.isoformat()

        additional_info = self.additional_info

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "planned_quantity": planned_quantity,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_transaction import BatchTransaction

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        planned_quantity = d.pop("planned_quantity")

        _status = d.pop("status", UNSET)
        status: CreateManufacturingOrderRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreateManufacturingOrderRequestStatus(_status)

        order_no = d.pop("order_no", UNSET)

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

        create_manufacturing_order_request = cls(
            variant_id=variant_id,
            location_id=location_id,
            planned_quantity=planned_quantity,
            status=status,
            order_no=order_no,
            actual_quantity=actual_quantity,
            order_created_date=order_created_date,
            production_deadline_date=production_deadline_date,
            additional_info=additional_info,
            batch_transactions=batch_transactions,
        )

        create_manufacturing_order_request.additional_properties = d
        return create_manufacturing_order_request

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
