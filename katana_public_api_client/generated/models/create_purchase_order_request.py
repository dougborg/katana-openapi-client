from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.create_purchase_order_request_entity_type import (
    CreatePurchaseOrderRequestEntityType,
)
from ..models.create_purchase_order_request_status import (
    CreatePurchaseOrderRequestStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_row_request import PurchaseOrderRowRequest


T = TypeVar("T", bound="CreatePurchaseOrderRequest")


@_attrs_define
class CreatePurchaseOrderRequest:
    order_no: str
    supplier_id: int
    location_id: int
    purchase_order_rows: list["PurchaseOrderRowRequest"]
    entity_type: Unset | CreatePurchaseOrderRequestEntityType = UNSET
    currency: Unset | str = UNSET
    status: Unset | CreatePurchaseOrderRequestStatus = UNSET
    expected_arrival_date: Unset | str = UNSET
    order_created_date: Unset | str = UNSET
    tracking_location_id: Unset | int = UNSET
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

        expected_arrival_date = self.expected_arrival_date

        order_created_date = self.order_created_date

        tracking_location_id = self.tracking_location_id

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
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if tracking_location_id is not UNSET:
            field_dict["tracking_location_id"] = tracking_location_id
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

        expected_arrival_date = d.pop("expected_arrival_date", UNSET)

        order_created_date = d.pop("order_created_date", UNSET)

        tracking_location_id = d.pop("tracking_location_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        create_purchase_order_request = cls(
            order_no=order_no,
            supplier_id=supplier_id,
            location_id=location_id,
            purchase_order_rows=purchase_order_rows,
            entity_type=entity_type,
            currency=currency,
            status=status,
            expected_arrival_date=expected_arrival_date,
            order_created_date=order_created_date,
            tracking_location_id=tracking_location_id,
            additional_info=additional_info,
        )

        return create_purchase_order_request
