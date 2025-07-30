import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.sales_order_ingredient_availability_type_0 import (
    SalesOrderIngredientAvailabilityType0,
)
from ..models.sales_order_product_availability_type_0 import (
    SalesOrderProductAvailabilityType0,
)
from ..models.sales_order_production_status_type_0 import (
    SalesOrderProductionStatusType0,
)
from ..models.sales_order_status import SalesOrderStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_address import SalesOrderAddress
    from ..models.sales_order_row import SalesOrderRow


T = TypeVar("T", bound="SalesOrder")


@_attrs_define
class SalesOrder:
    id: int
    customer_id: int
    order_no: str
    location_id: int
    status: SalesOrderStatus
    source: None | Unset | str = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    delivery_date: None | Unset | datetime.datetime = UNSET
    picked_date: None | Unset | datetime.datetime = UNSET
    currency: Unset | str = UNSET
    conversion_rate: None | Unset | float = UNSET
    conversion_date: None | Unset | datetime.datetime = UNSET
    invoicing_status: None | Unset | str = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    additional_info: None | Unset | str = UNSET
    customer_ref: None | Unset | str = UNSET
    sales_order_rows: Unset | list["SalesOrderRow"] = UNSET
    ecommerce_order_type: None | Unset | str = UNSET
    ecommerce_store_name: None | Unset | str = UNSET
    ecommerce_order_id: None | Unset | str = UNSET
    product_availability: None | SalesOrderProductAvailabilityType0 | Unset = UNSET
    product_expected_date: None | Unset | datetime.datetime = UNSET
    ingredient_availability: None | SalesOrderIngredientAvailabilityType0 | Unset = (
        UNSET
    )
    ingredient_expected_date: None | Unset | datetime.datetime = UNSET
    production_status: None | SalesOrderProductionStatusType0 | Unset = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET
    billing_address_id: None | Unset | int = UNSET
    shipping_address_id: None | Unset | int = UNSET
    addresses: Unset | list["SalesOrderAddress"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        customer_id = self.customer_id

        order_no = self.order_no

        location_id = self.location_id

        status = self.status.value

        source: None | Unset | str
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        delivery_date: None | Unset | str
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        elif isinstance(self.delivery_date, datetime.datetime):
            delivery_date = self.delivery_date.isoformat()
        else:
            delivery_date = self.delivery_date

        picked_date: None | Unset | str
        if isinstance(self.picked_date, Unset):
            picked_date = UNSET
        elif isinstance(self.picked_date, datetime.datetime):
            picked_date = self.picked_date.isoformat()
        else:
            picked_date = self.picked_date

        currency = self.currency

        conversion_rate: None | Unset | float
        if isinstance(self.conversion_rate, Unset):
            conversion_rate = UNSET
        else:
            conversion_rate = self.conversion_rate

        conversion_date: None | Unset | str
        if isinstance(self.conversion_date, Unset):
            conversion_date = UNSET
        elif isinstance(self.conversion_date, datetime.datetime):
            conversion_date = self.conversion_date.isoformat()
        else:
            conversion_date = self.conversion_date

        invoicing_status: None | Unset | str
        if isinstance(self.invoicing_status, Unset):
            invoicing_status = UNSET
        else:
            invoicing_status = self.invoicing_status

        total = self.total

        total_in_base_currency = self.total_in_base_currency

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

        sales_order_rows: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.sales_order_rows, Unset):
            sales_order_rows = []
            for sales_order_rows_item_data in self.sales_order_rows:
                sales_order_rows_item = sales_order_rows_item_data.to_dict()
                sales_order_rows.append(sales_order_rows_item)

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

        product_availability: None | Unset | str
        if isinstance(self.product_availability, Unset):
            product_availability = UNSET
        elif isinstance(self.product_availability, SalesOrderProductAvailabilityType0):
            product_availability = self.product_availability.value
        else:
            product_availability = self.product_availability

        product_expected_date: None | Unset | str
        if isinstance(self.product_expected_date, Unset):
            product_expected_date = UNSET
        elif isinstance(self.product_expected_date, datetime.datetime):
            product_expected_date = self.product_expected_date.isoformat()
        else:
            product_expected_date = self.product_expected_date

        ingredient_availability: None | Unset | str
        if isinstance(self.ingredient_availability, Unset):
            ingredient_availability = UNSET
        elif isinstance(
            self.ingredient_availability, SalesOrderIngredientAvailabilityType0
        ):
            ingredient_availability = self.ingredient_availability.value
        else:
            ingredient_availability = self.ingredient_availability

        ingredient_expected_date: None | Unset | str
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        elif isinstance(self.ingredient_expected_date, datetime.datetime):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()
        else:
            ingredient_expected_date = self.ingredient_expected_date

        production_status: None | Unset | str
        if isinstance(self.production_status, Unset):
            production_status = UNSET
        elif isinstance(self.production_status, SalesOrderProductionStatusType0):
            production_status = self.production_status.value
        else:
            production_status = self.production_status

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

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

        billing_address_id: None | Unset | int
        if isinstance(self.billing_address_id, Unset):
            billing_address_id = UNSET
        else:
            billing_address_id = self.billing_address_id

        shipping_address_id: None | Unset | int
        if isinstance(self.shipping_address_id, Unset):
            shipping_address_id = UNSET
        else:
            shipping_address_id = self.shipping_address_id

        addresses: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.addresses, Unset):
            addresses = []
            for addresses_item_data in self.addresses:
                addresses_item = addresses_item_data.to_dict()
                addresses.append(addresses_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "customer_id": customer_id,
                "order_no": order_no,
                "location_id": location_id,
                "status": status,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if picked_date is not UNSET:
            field_dict["picked_date"] = picked_date
        if currency is not UNSET:
            field_dict["currency"] = currency
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if invoicing_status is not UNSET:
            field_dict["invoicing_status"] = invoicing_status
        if total is not UNSET:
            field_dict["total"] = total
        if total_in_base_currency is not UNSET:
            field_dict["total_in_base_currency"] = total_in_base_currency
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if customer_ref is not UNSET:
            field_dict["customer_ref"] = customer_ref
        if sales_order_rows is not UNSET:
            field_dict["sales_order_rows"] = sales_order_rows
        if ecommerce_order_type is not UNSET:
            field_dict["ecommerce_order_type"] = ecommerce_order_type
        if ecommerce_store_name is not UNSET:
            field_dict["ecommerce_store_name"] = ecommerce_store_name
        if ecommerce_order_id is not UNSET:
            field_dict["ecommerce_order_id"] = ecommerce_order_id
        if product_availability is not UNSET:
            field_dict["product_availability"] = product_availability
        if product_expected_date is not UNSET:
            field_dict["product_expected_date"] = product_expected_date
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date
        if production_status is not UNSET:
            field_dict["production_status"] = production_status
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_number_url is not UNSET:
            field_dict["tracking_number_url"] = tracking_number_url
        if billing_address_id is not UNSET:
            field_dict["billing_address_id"] = billing_address_id
        if shipping_address_id is not UNSET:
            field_dict["shipping_address_id"] = shipping_address_id
        if addresses is not UNSET:
            field_dict["addresses"] = addresses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_address import SalesOrderAddress
        from ..models.sales_order_row import SalesOrderRow

        d = dict(src_dict)
        id = d.pop("id")

        customer_id = d.pop("customer_id")

        order_no = d.pop("order_no")

        location_id = d.pop("location_id")

        status = SalesOrderStatus(d.pop("status"))

        def _parse_source(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        source = _parse_source(d.pop("source", UNSET))

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

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

        def _parse_picked_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                picked_date_type_0 = isoparse(data)

                return picked_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        picked_date = _parse_picked_date(d.pop("picked_date", UNSET))

        currency = d.pop("currency", UNSET)

        def _parse_conversion_rate(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        conversion_rate = _parse_conversion_rate(d.pop("conversion_rate", UNSET))

        def _parse_conversion_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                conversion_date_type_0 = isoparse(data)

                return conversion_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        conversion_date = _parse_conversion_date(d.pop("conversion_date", UNSET))

        def _parse_invoicing_status(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        invoicing_status = _parse_invoicing_status(d.pop("invoicing_status", UNSET))

        total = d.pop("total", UNSET)

        total_in_base_currency = d.pop("total_in_base_currency", UNSET)

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

        sales_order_rows = []
        _sales_order_rows = d.pop("sales_order_rows", UNSET)
        for sales_order_rows_item_data in _sales_order_rows or []:
            sales_order_rows_item = SalesOrderRow.from_dict(sales_order_rows_item_data)

            sales_order_rows.append(sales_order_rows_item)

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

        def _parse_product_availability(
            data: object,
        ) -> None | SalesOrderProductAvailabilityType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                product_availability_type_0 = SalesOrderProductAvailabilityType0(data)

                return product_availability_type_0
            except:  # noqa: E722
                pass
            return cast(None | SalesOrderProductAvailabilityType0 | Unset, data)

        product_availability = _parse_product_availability(
            d.pop("product_availability", UNSET)
        )

        def _parse_product_expected_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                product_expected_date_type_0 = isoparse(data)

                return product_expected_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        product_expected_date = _parse_product_expected_date(
            d.pop("product_expected_date", UNSET)
        )

        def _parse_ingredient_availability(
            data: object,
        ) -> None | SalesOrderIngredientAvailabilityType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_availability_type_0 = SalesOrderIngredientAvailabilityType0(
                    data
                )

                return ingredient_availability_type_0
            except:  # noqa: E722
                pass
            return cast(None | SalesOrderIngredientAvailabilityType0 | Unset, data)

        ingredient_availability = _parse_ingredient_availability(
            d.pop("ingredient_availability", UNSET)
        )

        def _parse_ingredient_expected_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_expected_date_type_0 = isoparse(data)

                return ingredient_expected_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        ingredient_expected_date = _parse_ingredient_expected_date(
            d.pop("ingredient_expected_date", UNSET)
        )

        def _parse_production_status(
            data: object,
        ) -> None | SalesOrderProductionStatusType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                production_status_type_0 = SalesOrderProductionStatusType0(data)

                return production_status_type_0
            except:  # noqa: E722
                pass
            return cast(None | SalesOrderProductionStatusType0 | Unset, data)

        production_status = _parse_production_status(d.pop("production_status", UNSET))

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

        def _parse_billing_address_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        billing_address_id = _parse_billing_address_id(
            d.pop("billing_address_id", UNSET)
        )

        def _parse_shipping_address_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        shipping_address_id = _parse_shipping_address_id(
            d.pop("shipping_address_id", UNSET)
        )

        addresses = []
        _addresses = d.pop("addresses", UNSET)
        for addresses_item_data in _addresses or []:
            addresses_item = SalesOrderAddress.from_dict(addresses_item_data)

            addresses.append(addresses_item)

        sales_order = cls(
            id=id,
            customer_id=customer_id,
            order_no=order_no,
            location_id=location_id,
            status=status,
            source=source,
            order_created_date=order_created_date,
            delivery_date=delivery_date,
            picked_date=picked_date,
            currency=currency,
            conversion_rate=conversion_rate,
            conversion_date=conversion_date,
            invoicing_status=invoicing_status,
            total=total,
            total_in_base_currency=total_in_base_currency,
            additional_info=additional_info,
            customer_ref=customer_ref,
            sales_order_rows=sales_order_rows,
            ecommerce_order_type=ecommerce_order_type,
            ecommerce_store_name=ecommerce_store_name,
            ecommerce_order_id=ecommerce_order_id,
            product_availability=product_availability,
            product_expected_date=product_expected_date,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            production_status=production_status,
            created_at=created_at,
            updated_at=updated_at,
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
            billing_address_id=billing_address_id,
            shipping_address_id=shipping_address_id,
            addresses=addresses,
        )

        sales_order.additional_properties = d
        return sales_order

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
