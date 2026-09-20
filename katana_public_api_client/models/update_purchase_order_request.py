from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.purchase_order_status import PurchaseOrderStatus

if TYPE_CHECKING:
    from ..models.update_purchase_order_request_custom_fields_type_0 import (
        UpdatePurchaseOrderRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdatePurchaseOrderRequest")


@_attrs_define
class UpdatePurchaseOrderRequest:
    """Request payload for updating an existing purchase order's details, status, and line items

    Example:
        {'order_no': 'PO-2024-0156-REVISED', 'expected_arrival_date': '2024-02-20T00:00:00Z', 'status':
            'PARTIALLY_RECEIVED', 'additional_info': 'Delivery delayed due to weather - updated schedule'}
    """

    custom_fields: Unset | UpdatePurchaseOrderRequestCustomFieldsType0 | None = UNSET
    order_no: str | Unset = UNSET
    supplier_id: int | Unset = UNSET
    currency: str | Unset = UNSET
    tracking_location_id: int | Unset = UNSET
    status: PurchaseOrderStatus | Unset = UNSET
    expected_arrival_date: datetime.datetime | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    location_id: int | Unset = UNSET
    additional_info: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_purchase_order_request_custom_fields_type_0 import (
            UpdatePurchaseOrderRequestCustomFieldsType0,
        )

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, UpdatePurchaseOrderRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        order_no = self.order_no

        supplier_id = self.supplier_id

        currency = self.currency

        tracking_location_id = self.tracking_location_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        expected_arrival_date: str | Unset = UNSET
        if not isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = self.expected_arrival_date.isoformat()

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        location_id = self.location_id

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if tracking_location_id is not UNSET:
            field_dict["tracking_location_id"] = tracking_location_id
        if status is not UNSET:
            field_dict["status"] = status
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_purchase_order_request_custom_fields_type_0 import (
            UpdatePurchaseOrderRequestCustomFieldsType0,
        )

        d = dict(src_dict)

        def _parse_custom_fields(
            data: object,
        ) -> Unset | UpdatePurchaseOrderRequestCustomFieldsType0 | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    UpdatePurchaseOrderRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                Unset | UpdatePurchaseOrderRequestCustomFieldsType0 | None, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        order_no = d.pop("order_no", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        currency = d.pop("currency", UNSET)

        tracking_location_id = d.pop("tracking_location_id", UNSET)

        _status = d.pop("status", UNSET)
        status: PurchaseOrderStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = PurchaseOrderStatus(_status)

        _expected_arrival_date = d.pop("expected_arrival_date", UNSET)
        expected_arrival_date: datetime.datetime | Unset
        if isinstance(_expected_arrival_date, Unset):
            expected_arrival_date = UNSET
        else:
            expected_arrival_date = datetime.datetime.fromisoformat(
                _expected_arrival_date
            )

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: datetime.datetime | Unset
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = datetime.datetime.fromisoformat(_order_created_date)

        location_id = d.pop("location_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        update_purchase_order_request = cls(
            custom_fields=custom_fields,
            order_no=order_no,
            supplier_id=supplier_id,
            currency=currency,
            tracking_location_id=tracking_location_id,
            status=status,
            expected_arrival_date=expected_arrival_date,
            order_created_date=order_created_date,
            location_id=location_id,
            additional_info=additional_info,
        )

        return update_purchase_order_request
