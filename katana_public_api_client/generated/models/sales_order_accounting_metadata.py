import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.sales_order_accounting_metadata_integration_type import (
    SalesOrderAccountingMetadataIntegrationType,
)

T = TypeVar("T", bound="SalesOrderAccountingMetadata")


@_attrs_define
class SalesOrderAccountingMetadata:
    """Accounting integration metadata linking sales orders to external accounting systems and invoice records

    Example:
        {'id': 2901, 'sales_order_id': 2001, 'fulfillment_id': 2701, 'invoice_id': 'INV-2024-001', 'integration_type':
            'xero', 'created_at': '2024-01-20T17:00:00Z'}

    Attributes:
        id (int): Unique identifier for the accounting metadata record
        sales_order_id (int): ID of the sales order linked to accounting system
        fulfillment_id (int): ID of the fulfillment record associated with this accounting entry
        invoice_id (str): Invoice identifier in the external accounting system
        integration_type (SalesOrderAccountingMetadataIntegrationType): Type of accounting system integration used
        created_at (datetime.datetime): Date and time when the accounting metadata was created
    """

    id: int
    sales_order_id: int
    fulfillment_id: int
    invoice_id: str
    integration_type: SalesOrderAccountingMetadataIntegrationType
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_order_id = self.sales_order_id

        fulfillment_id = self.fulfillment_id

        invoice_id = self.invoice_id

        integration_type = self.integration_type.value

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sales_order_id": sales_order_id,
                "fulfillment_id": fulfillment_id,
                "invoice_id": invoice_id,
                "integration_type": integration_type,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        sales_order_id = d.pop("sales_order_id")

        fulfillment_id = d.pop("fulfillment_id")

        invoice_id = d.pop("invoice_id")

        integration_type = SalesOrderAccountingMetadataIntegrationType(
            d.pop("integration_type")
        )

        created_at = isoparse(d.pop("created_at"))

        sales_order_accounting_metadata = cls(
            id=id,
            sales_order_id=sales_order_id,
            fulfillment_id=fulfillment_id,
            invoice_id=invoice_id,
            integration_type=integration_type,
            created_at=created_at,
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
