import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.create_sales_order_request_status import CreateSalesOrderRequestStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_sales_order_request_addresses_item import (
        CreateSalesOrderRequestAddressesItem,
    )
    from ..models.create_sales_order_request_sales_order_rows_item import (
        CreateSalesOrderRequestSalesOrderRowsItem,
    )


T = TypeVar("T", bound="CreateSalesOrderRequest")


@_attrs_define
class CreateSalesOrderRequest:
    """Request payload for creating a new sales order

    Example:
        {'order_no': 'SO-2024-002', 'customer_id': 201, 'location_id': 1, 'sales_order_rows': [{'quantity': 3.0,
            'variant_id': 2001, 'tax_rate_id': 101, 'price_per_unit': 199.99, 'attributes': [{'key': 'gift_wrap', 'value':
            'premium'}]}, {'quantity': 2.0, 'variant_id': 2002, 'tax_rate_id': 101, 'price_per_unit': 149.99}], 'addresses':
            [{'entity_type': 'billing', 'first_name': 'John', 'last_name': 'Smith', 'company': 'Tech Solutions Inc',
            'line_1': '123 Business Ave', 'city': 'New York', 'state': 'NY', 'zip': '10001', 'country': 'United States'},
            {'entity_type': 'shipping', 'first_name': 'John', 'last_name': 'Smith', 'company': 'Tech Solutions Inc',
            'line_1': '456 Delivery St', 'city': 'New York', 'state': 'NY', 'zip': '10002', 'country': 'United States'}],
            'order_created_date': '2024-02-01T11:00:00Z', 'delivery_date': '2024-02-15T12:00:00Z', 'currency': 'USD',
            'status': 'PENDING', 'additional_info': 'Rush order - customer needs by Feb 15th', 'customer_ref': 'CUST-
            ORDER-456', 'ecommerce_order_type': 'shopify', 'ecommerce_store_name': 'Premium Electronics Store',
            'ecommerce_order_id': 'SHOP-456789'}
    """

    order_no: str
    customer_id: int
    sales_order_rows: list["CreateSalesOrderRequestSalesOrderRowsItem"]
    location_id: int
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET
    addresses: Unset | list["CreateSalesOrderRequestAddressesItem"] = UNSET
    order_created_date: None | Unset | datetime.datetime = UNSET
    delivery_date: None | Unset | datetime.datetime = UNSET
    currency: None | Unset | str = UNSET
    status: Unset | CreateSalesOrderRequestStatus = UNSET
    additional_info: None | Unset | str = UNSET
    customer_ref: None | Unset | str = UNSET
    ecommerce_order_type: None | Unset | str = UNSET
    ecommerce_store_name: None | Unset | str = UNSET
    ecommerce_order_id: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        customer_id = self.customer_id

        sales_order_rows = []
        for sales_order_rows_item_data in self.sales_order_rows:
            sales_order_rows_item = sales_order_rows_item_data.to_dict()
            sales_order_rows.append(sales_order_rows_item)

        location_id = self.location_id

        tracking_number: None | Unset | str
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        else:
            tracking_number = self.tracking_number

        tracking_number_url: None | Unset | str
        if isinstance(self.tracking_number_url, Unset):
            tracking_number_url = UNSET
        else:
            tracking_number_url = self.tracking_number_url

        addresses: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.addresses, Unset):
            addresses = []
            for addresses_item_data in self.addresses:
                addresses_item = addresses_item_data.to_dict()
                addresses.append(addresses_item)

        order_created_date: None | Unset | str
        if isinstance(self.order_created_date, Unset):
            order_created_date = UNSET
        elif isinstance(self.order_created_date, datetime.datetime):
            order_created_date = self.order_created_date.isoformat()
        else:
            order_created_date = self.order_created_date

        delivery_date: None | Unset | str
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        elif isinstance(self.delivery_date, datetime.datetime):
            delivery_date = self.delivery_date.isoformat()
        else:
            delivery_date = self.delivery_date

        currency: None | Unset | str
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        customer_ref: None | Unset | str
        if isinstance(self.customer_ref, Unset):
            customer_ref = UNSET
        else:
            customer_ref = self.customer_ref

        ecommerce_order_type: None | Unset | str
        if isinstance(self.ecommerce_order_type, Unset):
            ecommerce_order_type = UNSET
        else:
            ecommerce_order_type = self.ecommerce_order_type

        ecommerce_store_name: None | Unset | str
        if isinstance(self.ecommerce_store_name, Unset):
            ecommerce_store_name = UNSET
        else:
            ecommerce_store_name = self.ecommerce_store_name

        ecommerce_order_id: None | Unset | str
        if isinstance(self.ecommerce_order_id, Unset):
            ecommerce_order_id = UNSET
        else:
            ecommerce_order_id = self.ecommerce_order_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "order_no": order_no,
                "customer_id": customer_id,
                "sales_order_rows": sales_order_rows,
                "location_id": location_id,
            }
        )
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_number_url is not UNSET:
            field_dict["tracking_number_url"] = tracking_number_url
        if addresses is not UNSET:
            field_dict["addresses"] = addresses
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if currency is not UNSET:
            field_dict["currency"] = currency
        if status is not UNSET:
            field_dict["status"] = status
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if customer_ref is not UNSET:
            field_dict["customer_ref"] = customer_ref
        if ecommerce_order_type is not UNSET:
            field_dict["ecommerce_order_type"] = ecommerce_order_type
        if ecommerce_store_name is not UNSET:
            field_dict["ecommerce_store_name"] = ecommerce_store_name
        if ecommerce_order_id is not UNSET:
            field_dict["ecommerce_order_id"] = ecommerce_order_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_sales_order_request_addresses_item import (
            CreateSalesOrderRequestAddressesItem,
        )
        from ..models.create_sales_order_request_sales_order_rows_item import (
            CreateSalesOrderRequestSalesOrderRowsItem,
        )

        d = dict(src_dict)
        order_no = d.pop("order_no")

        customer_id = d.pop("customer_id")

        sales_order_rows = []
        _sales_order_rows = d.pop("sales_order_rows")
        for sales_order_rows_item_data in _sales_order_rows:
            sales_order_rows_item = CreateSalesOrderRequestSalesOrderRowsItem.from_dict(
                sales_order_rows_item_data
            )

            sales_order_rows.append(sales_order_rows_item)

        location_id = d.pop("location_id")

        def _parse_tracking_number(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_tracking_number_url(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        tracking_number_url = _parse_tracking_number_url(
            d.pop("tracking_number_url", UNSET)
        )

        addresses = []
        _addresses = d.pop("addresses", UNSET)
        for addresses_item_data in _addresses or []:
            addresses_item = CreateSalesOrderRequestAddressesItem.from_dict(
                addresses_item_data
            )

            addresses.append(addresses_item)

        def _parse_order_created_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                order_created_date_type_0 = isoparse(data)

                return order_created_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        order_created_date = _parse_order_created_date(
            d.pop("order_created_date", UNSET)
        )

        def _parse_delivery_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                delivery_date_type_0 = isoparse(data)

                return delivery_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

        def _parse_currency(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        _status = d.pop("status", UNSET)
        status: Unset | CreateSalesOrderRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreateSalesOrderRequestStatus(_status)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        def _parse_customer_ref(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))

        def _parse_ecommerce_order_type(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        ecommerce_order_type = _parse_ecommerce_order_type(
            d.pop("ecommerce_order_type", UNSET)
        )

        def _parse_ecommerce_store_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        ecommerce_store_name = _parse_ecommerce_store_name(
            d.pop("ecommerce_store_name", UNSET)
        )

        def _parse_ecommerce_order_id(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        ecommerce_order_id = _parse_ecommerce_order_id(
            d.pop("ecommerce_order_id", UNSET)
        )

        create_sales_order_request = cls(
            order_no=order_no,
            customer_id=customer_id,
            sales_order_rows=sales_order_rows,
            location_id=location_id,
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
            addresses=addresses,
            order_created_date=order_created_date,
            delivery_date=delivery_date,
            currency=currency,
            status=status,
            additional_info=additional_info,
            customer_ref=customer_ref,
            ecommerce_order_type=ecommerce_order_type,
            ecommerce_store_name=ecommerce_store_name,
            ecommerce_order_id=ecommerce_order_id,
        )

        return create_sales_order_request
