import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_sales_return_row_request import CreateSalesReturnRowRequest


T = TypeVar("T", bound="CreateSalesReturnRequest")


@_attrs_define
class CreateSalesReturnRequest:
    customer_id: int
    order_no: str
    return_location_id: int
    sales_return_rows: list["CreateSalesReturnRowRequest"]
    sales_order_id: Unset | int = UNSET
    currency: Unset | str = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        customer_id = self.customer_id

        order_no = self.order_no

        return_location_id = self.return_location_id

        sales_return_rows = []
        for sales_return_rows_item_data in self.sales_return_rows:
            sales_return_rows_item = sales_return_rows_item_data.to_dict()
            sales_return_rows.append(sales_return_rows_item)

        sales_order_id = self.sales_order_id

        currency = self.currency

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "customer_id": customer_id,
                "order_no": order_no,
                "return_location_id": return_location_id,
                "sales_return_rows": sales_return_rows,
            }
        )
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_sales_return_row_request import CreateSalesReturnRowRequest

        d = dict(src_dict)
        customer_id = d.pop("customer_id")

        order_no = d.pop("order_no")

        return_location_id = d.pop("return_location_id")

        sales_return_rows = []
        _sales_return_rows = d.pop("sales_return_rows")
        for sales_return_rows_item_data in _sales_return_rows:
            sales_return_rows_item = CreateSalesReturnRowRequest.from_dict(
                sales_return_rows_item_data
            )

            sales_return_rows.append(sales_return_rows_item)

        sales_order_id = d.pop("sales_order_id", UNSET)

        currency = d.pop("currency", UNSET)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        additional_info = d.pop("additional_info", UNSET)

        create_sales_return_request = cls(
            customer_id=customer_id,
            order_no=order_no,
            return_location_id=return_location_id,
            sales_return_rows=sales_return_rows,
            sales_order_id=sales_order_id,
            currency=currency,
            order_created_date=order_created_date,
            additional_info=additional_info,
        )

        return create_sales_return_request
