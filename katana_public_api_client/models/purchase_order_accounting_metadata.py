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
            {'id': 156, 'purchase_order_id': 8001, 'purchaseOrderId': 8001, 'porReceivedGroupId': 2001, 'integrationType':
                'quickbooks', 'billId': 'BILL-2024-001', 'createdAt': '2024-01-15T11:30:00Z'}

        Attributes:
            id (int): Unique identifier for the accounting metadata record
            purchaseOrderId (int): Alternative purchase order ID field for accounting system compatibility
            purchase_order_id (Union[Unset, int]): ID of the purchase order linked to the accounting system
            por_received_group_id (Union[Unset, int]): ID of the received items group for accounting cost allocation
            integration_type (Union[Unset, str]): Type of accounting system integration (e.g., quickbooks, xero, sage)
            bill_id (Union[Unset, str]): Bill identifier in the external accounting system
            created_at (Union[Unset, datetime.datetime]): Date and time when the accounting metadata was created
    """

    id: int
    purchaseOrderId: int
    purchase_order_id: Unset | int = UNSET
    por_received_group_id: Unset | int = UNSET
    integration_type: Unset | str = UNSET
    bill_id: Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        purchaseOrderId = self.purchaseOrderId

        purchase_order_id = self.purchase_order_id

        por_received_group_id = self.por_received_group_id

        integration_type = self.integration_type

        bill_id = self.bill_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "purchaseOrderId": purchaseOrderId,
            }
        )
        if purchase_order_id is not UNSET:
            field_dict["purchase_order_id"] = purchase_order_id
        if por_received_group_id is not UNSET:
            field_dict["porReceivedGroupId"] = por_received_group_id
        if integration_type is not UNSET:
            field_dict["integrationType"] = integration_type
        if bill_id is not UNSET:
            field_dict["billId"] = bill_id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        purchaseOrderId = d.pop("purchaseOrderId")

        purchase_order_id = d.pop("purchase_order_id", UNSET)

        por_received_group_id = d.pop("porReceivedGroupId", UNSET)

        integration_type = d.pop("integrationType", UNSET)

        bill_id = d.pop("billId", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        purchase_order_accounting_metadata = cls(
            id=id,
            purchaseOrderId=purchaseOrderId,
            purchase_order_id=purchase_order_id,
            por_received_group_id=por_received_group_id,
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
