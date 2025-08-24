import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.create_purchase_order_request_entity_type import (
    CreatePurchaseOrderRequestEntityType,
)
from ..models.create_purchase_order_request_status import (
    CreatePurchaseOrderRequestStatus,
)

if TYPE_CHECKING:
    from ..models.purchase_order_row_request import PurchaseOrderRowRequest


T = TypeVar("T", bound="CreatePurchaseOrderRequest")


@_attrs_define
class CreatePurchaseOrderRequest:
    """Request payload for creating a new purchase order to procure materials or products from suppliers

    Example:
        {'order_no': 'PO-2024-0156', 'entity_type': 'regular', 'supplier_id': 4001, 'currency': 'USD', 'status':
            'NOT_RECEIVED', 'order_created_date': '2024-01-15T09:30:00Z', 'location_id': 1, 'additional_info': "Rush order -
            needed for Valentine's Day production run", 'purchase_order_rows': [{'quantity': 250, 'price_per_unit': 2.85,
            'variant_id': 501, 'tax_rate_id': 1, 'purchase_uom': 'kg', 'purchase_uom_conversion_rate': 1.0, 'arrival_date':
            '2024-08-20T14:45:00Z'}, {'quantity': 100, 'price_per_unit': 12.5, 'variant_id': 502, 'tax_rate_id': 1,
            'purchase_uom': 'pieces', 'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}]}

    Attributes:
        order_no (str): Unique purchase order number for tracking and reference
        supplier_id (int): Unique identifier of the supplier providing the materials or services
        location_id (int): Primary location where the purchased items will be received and stored
        purchase_order_rows (list['PurchaseOrderRowRequest']): List of line items being ordered, including quantities
            and pricing
        entity_type (Union[Unset, CreatePurchaseOrderRequestEntityType]): Type of purchase order - regular for materials
            or outsourced for subcontracted work
        currency (Union[Unset, str]): Active ISO 4217 currency code (e.g. USD, EUR).
        status (Union[Unset, CreatePurchaseOrderRequestStatus]): Initial status of the purchase order when created
        order_created_date (Union[Unset, datetime.datetime]): Date when the purchase order was created
        additional_info (Union[Unset, str]): Optional notes or special instructions for the supplier
    """

    order_no: str
    supplier_id: int
    location_id: int
    purchase_order_rows: list["PurchaseOrderRowRequest"]
    entity_type: Unset | CreatePurchaseOrderRequestEntityType = UNSET
    currency: Unset | str = UNSET
    status: Unset | CreatePurchaseOrderRequestStatus = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        supplier_id = self.supplier_id

        location_id = self.location_id

        purchase_order_rows = []
        for purchase_order_rows_item_data in self.purchase_order_rows:
            purchase_order_rows_item = purchase_order_rows_item_data.to_dict()
            purchase_order_rows.append(purchase_order_rows_item)

        entity_type: Unset | str = UNSET
        if not isinstance(self.entity_type, Unset):
            entity_type = self.entity_type.value

        currency = self.currency

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "order_no": order_no,
                "supplier_id": supplier_id,
                "location_id": location_id,
                "purchase_order_rows": purchase_order_rows,
            }
        )
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if currency is not UNSET:
            field_dict["currency"] = currency
        if status is not UNSET:
            field_dict["status"] = status
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_row_request import PurchaseOrderRowRequest

        d = dict(src_dict)
        order_no = d.pop("order_no")

        supplier_id = d.pop("supplier_id")

        location_id = d.pop("location_id")

        purchase_order_rows = []
        _purchase_order_rows = d.pop("purchase_order_rows")
        for purchase_order_rows_item_data in _purchase_order_rows:
            purchase_order_rows_item = PurchaseOrderRowRequest.from_dict(
                purchase_order_rows_item_data
            )

            purchase_order_rows.append(purchase_order_rows_item)

        _entity_type = d.pop("entity_type", UNSET)
        entity_type: Unset | CreatePurchaseOrderRequestEntityType
        if isinstance(_entity_type, Unset):
            entity_type = UNSET
        else:
            entity_type = CreatePurchaseOrderRequestEntityType(_entity_type)

        currency = d.pop("currency", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | CreatePurchaseOrderRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreatePurchaseOrderRequestStatus(_status)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        additional_info = d.pop("additional_info", UNSET)

        create_purchase_order_request = cls(
            order_no=order_no,
            supplier_id=supplier_id,
            location_id=location_id,
            purchase_order_rows=purchase_order_rows,
            entity_type=entity_type,
            currency=currency,
            status=status,
            order_created_date=order_created_date,
            additional_info=additional_info,
        )

        return create_purchase_order_request
