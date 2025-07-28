import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SalesOrderAccountingMetadata")


@_attrs_define
class SalesOrderAccountingMetadata:
    id: Unset | int = UNSET
    sales_order_id: Unset | int = UNSET
    external_id: Unset | str = UNSET
    accounting_system: Unset | str = UNSET
    sync_status: Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_order_id = self.sales_order_id

        external_id = self.external_id

        accounting_system = self.accounting_system

        sync_status = self.sync_status

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if accounting_system is not UNSET:
            field_dict["accounting_system"] = accounting_system
        if sync_status is not UNSET:
            field_dict["sync_status"] = sync_status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        sales_order_id = d.pop("sales_order_id", UNSET)

        external_id = d.pop("external_id", UNSET)

        accounting_system = d.pop("accounting_system", UNSET)

        sync_status = d.pop("sync_status", UNSET)

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

        sales_order_accounting_metadata = cls(
            id=id,
            sales_order_id=sales_order_id,
            external_id=external_id,
            accounting_system=accounting_system,
            sync_status=sync_status,
            created_at=created_at,
            updated_at=updated_at,
        )

        sales_order_accounting_metadata.additional_properties = d
        return sales_order_accounting_metadata

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
