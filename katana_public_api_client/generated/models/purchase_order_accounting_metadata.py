import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderAccountingMetadata")


@_attrs_define
class PurchaseOrderAccountingMetadata:
    id: Unset | int = UNSET
    purchase_order_id: Unset | int = UNSET
    purchaseOrderId: Unset | int = UNSET
    por_received_group_id: Unset | int = UNSET
    integration_type: Unset | str = UNSET
    bill_id: Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        purchase_order_id = self.purchase_order_id

        purchaseOrderId = self.purchaseOrderId

        por_received_group_id = self.por_received_group_id

        integration_type = self.integration_type

        bill_id = self.bill_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if purchase_order_id is not UNSET:
            field_dict["purchase_order_id"] = purchase_order_id
        if purchaseOrderId is not UNSET:
            field_dict["purchaseOrderId"] = purchaseOrderId
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
        id = d.pop("id", UNSET)

        purchase_order_id = d.pop("purchase_order_id", UNSET)

        purchaseOrderId = d.pop("purchaseOrderId", UNSET)

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
            purchase_order_id=purchase_order_id,
            purchaseOrderId=purchaseOrderId,
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
