from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.sales_order_fulfillment_invoice_status import (
    SalesOrderFulfillmentInvoiceStatus,
)
from ..models.sales_order_fulfillment_status import SalesOrderFulfillmentStatus

if TYPE_CHECKING:
    from ..models.sales_order_fulfillment_sales_order_fulfillment_rows_item import (
        SalesOrderFulfillmentSalesOrderFulfillmentRowsItem,
    )


T = TypeVar("T", bound="SalesOrderFulfillment")


@_attrs_define
class SalesOrderFulfillment:
    """Shipping and delivery record for a sales order, tracking the physical fulfillment process including picking,
    packing, and shipment tracking

        Example:
            {'id': 1, 'sales_order_id': 1, 'picked_date': '2020-10-23T10:37:05.085Z', 'status': 'DELIVERED',
                'invoice_status': 'NOT_INVOICED', 'conversion_rate': 2, 'conversion_date': '2020-10-23T10:37:05.085Z',
                'tracking_number': '12345678', 'tracking_url': 'https://tracking-number-url', 'tracking_carrier': 'UPS',
                'tracking_method': 'ground', 'packer_id': 1, 'sales_order_fulfillment_rows': [{'sales_order_row_id': 1,
                'quantity': 2, 'batch_transactions': [{'batch_id': 1, 'quantity': 2}], 'serial_numbers': [1]}], 'created_at':
                '2020-10-23T10:37:05.085Z', 'updated_at': '2020-10-23T10:37:05.085Z'}
    """

    id: int
    sales_order_id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    picked_date: datetime.datetime | None | Unset = UNSET
    status: SalesOrderFulfillmentStatus | Unset = UNSET
    invoice_status: SalesOrderFulfillmentInvoiceStatus | Unset = UNSET
    conversion_rate: float | None | Unset = UNSET
    conversion_date: datetime.datetime | None | Unset = UNSET
    tracking_number: None | str | Unset = UNSET
    tracking_url: None | str | Unset = UNSET
    tracking_carrier: None | str | Unset = UNSET
    tracking_method: None | str | Unset = UNSET
    packer_id: int | None | Unset = UNSET
    sales_order_fulfillment_rows: (
        list[SalesOrderFulfillmentSalesOrderFulfillmentRowsItem] | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_order_id = self.sales_order_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        picked_date: None | str | Unset
        if isinstance(self.picked_date, Unset):
            picked_date = UNSET
        elif isinstance(self.picked_date, datetime.datetime):
            picked_date = self.picked_date.isoformat()
        else:
            picked_date = self.picked_date

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        invoice_status: str | Unset = UNSET
        if not isinstance(self.invoice_status, Unset):
            invoice_status = self.invoice_status.value

        conversion_rate: float | None | Unset
        if isinstance(self.conversion_rate, Unset):
            conversion_rate = UNSET
        else:
            conversion_rate = self.conversion_rate

        conversion_date: None | str | Unset
        if isinstance(self.conversion_date, Unset):
            conversion_date = UNSET
        elif isinstance(self.conversion_date, datetime.datetime):
            conversion_date = self.conversion_date.isoformat()
        else:
            conversion_date = self.conversion_date

        tracking_number: None | str | Unset
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        else:
            tracking_number = self.tracking_number

        tracking_url: None | str | Unset
        if isinstance(self.tracking_url, Unset):
            tracking_url = UNSET
        else:
            tracking_url = self.tracking_url

        tracking_carrier: None | str | Unset
        if isinstance(self.tracking_carrier, Unset):
            tracking_carrier = UNSET
        else:
            tracking_carrier = self.tracking_carrier

        tracking_method: None | str | Unset
        if isinstance(self.tracking_method, Unset):
            tracking_method = UNSET
        else:
            tracking_method = self.tracking_method

        packer_id: int | None | Unset
        if isinstance(self.packer_id, Unset):
            packer_id = UNSET
        else:
            packer_id = self.packer_id

        sales_order_fulfillment_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.sales_order_fulfillment_rows, Unset):
            sales_order_fulfillment_rows = []
            for (
                sales_order_fulfillment_rows_item_data
            ) in self.sales_order_fulfillment_rows:
                sales_order_fulfillment_rows_item = (
                    sales_order_fulfillment_rows_item_data.to_dict()
                )
                sales_order_fulfillment_rows.append(sales_order_fulfillment_rows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sales_order_id": sales_order_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if picked_date is not UNSET:
            field_dict["picked_date"] = picked_date
        if status is not UNSET:
            field_dict["status"] = status
        if invoice_status is not UNSET:
            field_dict["invoice_status"] = invoice_status
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_url is not UNSET:
            field_dict["tracking_url"] = tracking_url
        if tracking_carrier is not UNSET:
            field_dict["tracking_carrier"] = tracking_carrier
        if tracking_method is not UNSET:
            field_dict["tracking_method"] = tracking_method
        if packer_id is not UNSET:
            field_dict["packer_id"] = packer_id
        if sales_order_fulfillment_rows is not UNSET:
            field_dict["sales_order_fulfillment_rows"] = sales_order_fulfillment_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_fulfillment_sales_order_fulfillment_rows_item import (
            SalesOrderFulfillmentSalesOrderFulfillmentRowsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        sales_order_id = d.pop("sales_order_id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_picked_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                picked_date_type_0 = isoparse(data)

                return picked_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        picked_date = _parse_picked_date(d.pop("picked_date", UNSET))

        _status = d.pop("status", UNSET)
        status: SalesOrderFulfillmentStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = SalesOrderFulfillmentStatus(_status)

        _invoice_status = d.pop("invoice_status", UNSET)
        invoice_status: SalesOrderFulfillmentInvoiceStatus | Unset
        if isinstance(_invoice_status, Unset):
            invoice_status = UNSET
        else:
            invoice_status = SalesOrderFulfillmentInvoiceStatus(_invoice_status)

        def _parse_conversion_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        conversion_rate = _parse_conversion_rate(d.pop("conversion_rate", UNSET))

        def _parse_conversion_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                conversion_date_type_0 = isoparse(data)

                return conversion_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        conversion_date = _parse_conversion_date(d.pop("conversion_date", UNSET))

        def _parse_tracking_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_tracking_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_url = _parse_tracking_url(d.pop("tracking_url", UNSET))

        def _parse_tracking_carrier(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_carrier = _parse_tracking_carrier(d.pop("tracking_carrier", UNSET))

        def _parse_tracking_method(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_method = _parse_tracking_method(d.pop("tracking_method", UNSET))

        def _parse_packer_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        packer_id = _parse_packer_id(d.pop("packer_id", UNSET))

        _sales_order_fulfillment_rows = d.pop("sales_order_fulfillment_rows", UNSET)
        sales_order_fulfillment_rows: (
            list[SalesOrderFulfillmentSalesOrderFulfillmentRowsItem] | Unset
        ) = UNSET
        if _sales_order_fulfillment_rows is not UNSET:
            sales_order_fulfillment_rows = []
            for sales_order_fulfillment_rows_item_data in _sales_order_fulfillment_rows:
                sales_order_fulfillment_rows_item = (
                    SalesOrderFulfillmentSalesOrderFulfillmentRowsItem.from_dict(
                        sales_order_fulfillment_rows_item_data
                    )
                )

                sales_order_fulfillment_rows.append(sales_order_fulfillment_rows_item)

        sales_order_fulfillment = cls(
            id=id,
            sales_order_id=sales_order_id,
            created_at=created_at,
            updated_at=updated_at,
            picked_date=picked_date,
            status=status,
            invoice_status=invoice_status,
            conversion_rate=conversion_rate,
            conversion_date=conversion_date,
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            tracking_carrier=tracking_carrier,
            tracking_method=tracking_method,
            packer_id=packer_id,
            sales_order_fulfillment_rows=sales_order_fulfillment_rows,
        )

        sales_order_fulfillment.additional_properties = d
        return sales_order_fulfillment

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
