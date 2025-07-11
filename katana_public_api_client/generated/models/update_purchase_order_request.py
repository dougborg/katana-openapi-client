from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_purchase_order_request_status import (
    UpdatePurchaseOrderRequestStatus,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePurchaseOrderRequest")


@_attrs_define
class UpdatePurchaseOrderRequest:
    """
    Attributes:
        order_no (Union[Unset, str]): Updatable only when status is in NOT_RECEIVED or PARTIALLY_RECEIVED
        supplier_id (Union[Unset, int]): Updatable only when status is in NOT_RECEIVED
        currency (Union[Unset, str]): Updatable only when status is in NOT_RECEIVED
        tracking_location_id (Union[Unset, int]): Updatable only when status is in NOT_RECEIVED and entity_type is
            outsourced
        status (Union[Unset, UpdatePurchaseOrderRequestStatus]):
        expected_arrival_date (Union[Unset, str]): Updatable only when status is in NOT_RECEIVED or PARTIALLY_RECEIVED.
            Update will override arrival_date on purchase order rows
        order_created_date (Union[Unset, str]):
        location_id (Union[Unset, int]): Updatable only when status is in NOT_RECEIVED
        additional_info (Union[Unset, str]):
    """

    order_no: Union[Unset, str] = UNSET
    supplier_id: Union[Unset, int] = UNSET
    currency: Union[Unset, str] = UNSET
    tracking_location_id: Union[Unset, int] = UNSET
    status: Union[Unset, UpdatePurchaseOrderRequestStatus] = UNSET
    expected_arrival_date: Union[Unset, str] = UNSET
    order_created_date: Union[Unset, str] = UNSET
    location_id: Union[Unset, int] = UNSET
    additional_info: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        supplier_id = self.supplier_id

        currency = self.currency

        tracking_location_id = self.tracking_location_id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        expected_arrival_date = self.expected_arrival_date

        order_created_date = self.order_created_date

        location_id = self.location_id

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
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
        d = dict(src_dict)
        order_no = d.pop("order_no", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        currency = d.pop("currency", UNSET)

        tracking_location_id = d.pop("tracking_location_id", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, UpdatePurchaseOrderRequestStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdatePurchaseOrderRequestStatus(_status)

        expected_arrival_date = d.pop("expected_arrival_date", UNSET)

        order_created_date = d.pop("order_created_date", UNSET)

        location_id = d.pop("location_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        update_purchase_order_request = cls(
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
