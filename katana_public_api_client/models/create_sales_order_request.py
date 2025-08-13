from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.create_sales_order_request_status import CreateSalesOrderRequestStatus

if TYPE_CHECKING:
    from ..models.create_sales_order_request_sales_order_rows_item import (
        CreateSalesOrderRequestSalesOrderRowsItem,
    )
    from ..models.sales_order_address import SalesOrderAddress


T = TypeVar("T", bound="CreateSalesOrderRequest")


@_attrs_define
class CreateSalesOrderRequest:
    """Request payload for creating a new sales order with customer information, order lines, and delivery details

    Example:
        {'order_no': 'SO-2024-002', 'customer_id': 1501, 'sales_order_rows': [{'quantity': 3, 'variant_id': 2101,
            'tax_rate_id': 301, 'location_id': 1, 'price_per_unit': 599.99, 'total_discount': 50.0, 'attributes': [{'key':
            'engrave_text', 'value': 'Professional Kitchen'}, {'key': 'rush_order', 'value': 'true'}]}], 'tracking_number':
            None, 'tracking_number_url': None, 'addresses': [{'entity_type': 'billing', 'first_name': 'David', 'last_name':
            'Wilson', 'company': "Wilson's Catering", 'line_1': '456 Commerce Ave', 'city': 'Seattle', 'state': 'WA', 'zip':
            '98101', 'country': 'US'}, {'entity_type': 'shipping', 'first_name': 'David', 'last_name': 'Wilson', 'company':
            "Wilson's Catering", 'line_1': '789 Industrial Blvd', 'city': 'Seattle', 'state': 'WA', 'zip': '98102',
            'country': 'US'}], 'order_created_date': '2024-01-16T09:00:00Z', 'delivery_date': '2024-01-23T15:00:00Z',
            'currency': 'USD', 'location_id': 1, 'status': 'PENDING', 'additional_info': 'Customer prefers morning
            delivery', 'customer_ref': 'WC-ORDER-2024-003', 'ecommerce_order_type': 'wholesale', 'ecommerce_store_name':
            'B2B Portal', 'ecommerce_order_id': 'B2B-7891-2024'}

    Attributes:
        order_no (str): Unique order number for tracking and reference
        customer_id (int): ID of the customer placing the order
        sales_order_rows (list['CreateSalesOrderRequestSalesOrderRowsItem']): List of products and quantities being
            ordered
        tracking_number (Union[None, Unset, str]): Shipping tracking number if already known
        tracking_number_url (Union[None, Unset, str]): URL for tracking shipment status
        addresses (Union[Unset, list['SalesOrderAddress']]): Billing and shipping addresses for the order
        order_created_date (Union[None, Unset, str]): Date when the order was originally created (defaults to current
            time)
        delivery_date (Union[None, Unset, str]): Requested delivery date
        currency (Union[None, Unset, str]): Currency code for the order (defaults to company base currency)
        location_id (Union[Unset, int]): Primary fulfillment location for the order
        status (Union[Unset, CreateSalesOrderRequestStatus]): Initial status of the order
        additional_info (Union[None, Unset, str]): Additional notes or instructions for the order
        customer_ref (Union[None, Unset, str]): Customer's internal reference number
        ecommerce_order_type (Union[None, Unset, str]): Type of ecommerce order if applicable
        ecommerce_store_name (Union[None, Unset, str]): Name of the ecommerce store if order originated from online
        ecommerce_order_id (Union[None, Unset, str]): Original order ID from the ecommerce platform
    """

    order_no: str
    customer_id: int
    sales_order_rows: list["CreateSalesOrderRequestSalesOrderRowsItem"]
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET
    addresses: Unset | list["SalesOrderAddress"] = UNSET
    order_created_date: None | Unset | str = UNSET
    delivery_date: None | Unset | str = UNSET
    currency: None | Unset | str = UNSET
    location_id: Unset | int = UNSET
    status: Unset | CreateSalesOrderRequestStatus = UNSET
    additional_info: None | Unset | str = UNSET
    customer_ref: None | Unset | str = UNSET
    ecommerce_order_type: None | Unset | str = UNSET
    ecommerce_store_name: None | Unset | str = UNSET
    ecommerce_order_id: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        customer_id = self.customer_id

        sales_order_rows = []
        for sales_order_rows_item_data in self.sales_order_rows:
            sales_order_rows_item = sales_order_rows_item_data.to_dict()
            sales_order_rows.append(sales_order_rows_item)

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
        else:
            order_created_date = self.order_created_date

        delivery_date: None | Unset | str
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        else:
            delivery_date = self.delivery_date

        currency: None | Unset | str
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        location_id = self.location_id

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
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "order_no": order_no,
                "customer_id": customer_id,
                "sales_order_rows": sales_order_rows,
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
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
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
        from ..models.create_sales_order_request_sales_order_rows_item import (
            CreateSalesOrderRequestSalesOrderRowsItem,
        )
        from ..models.sales_order_address import SalesOrderAddress

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
            addresses_item = SalesOrderAddress.from_dict(addresses_item_data)

            addresses.append(addresses_item)

        def _parse_order_created_date(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        order_created_date = _parse_order_created_date(
            d.pop("order_created_date", UNSET)
        )

        def _parse_delivery_date(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

        def _parse_currency(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        location_id = d.pop("location_id", UNSET)

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
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
            addresses=addresses,
            order_created_date=order_created_date,
            delivery_date=delivery_date,
            currency=currency,
            location_id=location_id,
            status=status,
            additional_info=additional_info,
            customer_ref=customer_ref,
            ecommerce_order_type=ecommerce_order_type,
            ecommerce_store_name=ecommerce_store_name,
            ecommerce_order_id=ecommerce_order_id,
        )

        create_sales_order_request.additional_properties = d
        return create_sales_order_request

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
