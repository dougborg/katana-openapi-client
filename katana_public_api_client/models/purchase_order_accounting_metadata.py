from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderAccountingMetadata")


@_attrs_define
class PurchaseOrderAccountingMetadata:
    """Accounting integration metadata linking purchase orders to external accounting systems for bill processing and
    financial record synchronization

        Example:
            {'id': 156, 'purchase_order_id': 8001, 'received_items_group_id': 2001, 'integration_type': 'quickBooks',
                'bill_id': 'BILL-2024-001', 'created_at': '2024-01-15T11:30:00Z'}
    """

    id: int
    purchase_order_id: int
    received_items_group_id: int | Unset = UNSET
    integration_type: str | Unset = UNSET
    bill_id: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        purchase_order_id = self.purchase_order_id

        received_items_group_id = self.received_items_group_id

        integration_type = self.integration_type

        bill_id = self.bill_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "purchase_order_id": purchase_order_id,
            }
        )
        if received_items_group_id is not UNSET:
            field_dict["received_items_group_id"] = received_items_group_id
        if integration_type is not UNSET:
            field_dict["integration_type"] = integration_type
        if bill_id is not UNSET:
            field_dict["bill_id"] = bill_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        purchase_order_id = d.pop("purchase_order_id")

        received_items_group_id = d.pop("received_items_group_id", UNSET)

        integration_type = d.pop("integration_type", UNSET)

        bill_id = d.pop("bill_id", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        purchase_order_accounting_metadata = cls(
            id=id,
            purchase_order_id=purchase_order_id,
            received_items_group_id=received_items_group_id,
            integration_type=integration_type,
            bill_id=bill_id,
            created_at=created_at,
        )

        purchase_order_accounting_metadata.additional_properties = d
        return purchase_order_accounting_metadata

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
