import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.sales_order_row_product_availability_type_0 import (
    SalesOrderRowProductAvailabilityType0,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_row_attributes_item import SalesOrderRowAttributesItem
    from ..models.sales_order_row_batch_transactions_item import (
        SalesOrderRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="SalesOrderRow")


@_attrs_define
class SalesOrderRow:
    id: int
    quantity: float
    variant_id: int
    tax_rate_id: None | Unset | int = UNSET
    location_id: None | Unset | int = UNSET
    product_availability: None | SalesOrderRowProductAvailabilityType0 | Unset = UNSET
    product_expected_date: None | Unset | datetime.datetime = UNSET
    price_per_unit: Unset | float = UNSET
    price_per_unit_in_base_currency: Unset | float = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    cogs_value: None | Unset | float = UNSET
    attributes: Unset | list["SalesOrderRowAttributesItem"] = UNSET
    batch_transactions: Unset | list["SalesOrderRowBatchTransactionsItem"] = UNSET
    serial_numbers: Unset | list[int] = UNSET
    linked_manufacturing_order_id: None | Unset | int = UNSET
    conversion_rate: None | Unset | float = UNSET
    conversion_date: None | Unset | datetime.datetime = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        quantity = self.quantity

        variant_id = self.variant_id

        tax_rate_id: None | Unset | int
        if isinstance(self.tax_rate_id, Unset):
            tax_rate_id = UNSET
        else:
            tax_rate_id = self.tax_rate_id

        location_id: None | Unset | int
        if isinstance(self.location_id, Unset):
            location_id = UNSET
        else:
            location_id = self.location_id

        product_availability: None | Unset | str
        if isinstance(self.product_availability, Unset):
            product_availability = UNSET
        elif isinstance(
            self.product_availability, SalesOrderRowProductAvailabilityType0
        ):
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

        price_per_unit = self.price_per_unit

        price_per_unit_in_base_currency = self.price_per_unit_in_base_currency

        total = self.total

        total_in_base_currency = self.total_in_base_currency

        cogs_value: None | Unset | float
        if isinstance(self.cogs_value, Unset):
            cogs_value = UNSET
        else:
            cogs_value = self.cogs_value

        attributes: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        serial_numbers: Unset | list[int] = UNSET
        if not isinstance(self.serial_numbers, Unset):
            serial_numbers = self.serial_numbers

        linked_manufacturing_order_id: None | Unset | int
        if isinstance(self.linked_manufacturing_order_id, Unset):
            linked_manufacturing_order_id = UNSET
        else:
            linked_manufacturing_order_id = self.linked_manufacturing_order_id

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

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "quantity": quantity,
                "variant_id": variant_id,
            }
        )
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if product_availability is not UNSET:
            field_dict["product_availability"] = product_availability
        if product_expected_date is not UNSET:
            field_dict["product_expected_date"] = product_expected_date
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if price_per_unit_in_base_currency is not UNSET:
            field_dict["price_per_unit_in_base_currency"] = (
                price_per_unit_in_base_currency
            )
        if total is not UNSET:
            field_dict["total"] = total
        if total_in_base_currency is not UNSET:
            field_dict["total_in_base_currency"] = total_in_base_currency
        if cogs_value is not UNSET:
            field_dict["cogs_value"] = cogs_value
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers
        if linked_manufacturing_order_id is not UNSET:
            field_dict["linked_manufacturing_order_id"] = linked_manufacturing_order_id
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_row_attributes_item import SalesOrderRowAttributesItem
        from ..models.sales_order_row_batch_transactions_item import (
            SalesOrderRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        quantity = d.pop("quantity")

        variant_id = d.pop("variant_id")

        def _parse_tax_rate_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        tax_rate_id = _parse_tax_rate_id(d.pop("tax_rate_id", UNSET))

        def _parse_location_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        location_id = _parse_location_id(d.pop("location_id", UNSET))

        def _parse_product_availability(
            data: object,
        ) -> None | SalesOrderRowProductAvailabilityType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                product_availability_type_0 = SalesOrderRowProductAvailabilityType0(
                    data
                )

                return product_availability_type_0
            except:  # noqa: E722
                pass
            return cast(None | SalesOrderRowProductAvailabilityType0 | Unset, data)

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

        price_per_unit = d.pop("price_per_unit", UNSET)

        price_per_unit_in_base_currency = d.pop(
            "price_per_unit_in_base_currency", UNSET
        )

        total = d.pop("total", UNSET)

        total_in_base_currency = d.pop("total_in_base_currency", UNSET)

        def _parse_cogs_value(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        cogs_value = _parse_cogs_value(d.pop("cogs_value", UNSET))

        attributes = []
        _attributes = d.pop("attributes", UNSET)
        for attributes_item_data in _attributes or []:
            attributes_item = SalesOrderRowAttributesItem.from_dict(
                attributes_item_data
            )

            attributes.append(attributes_item)

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = SalesOrderRowBatchTransactionsItem.from_dict(
                batch_transactions_item_data
            )

            batch_transactions.append(batch_transactions_item)

        serial_numbers = cast(list[int], d.pop("serial_numbers", UNSET))

        def _parse_linked_manufacturing_order_id(
            data: object,
        ) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        linked_manufacturing_order_id = _parse_linked_manufacturing_order_id(
            d.pop("linked_manufacturing_order_id", UNSET)
        )

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

        sales_order_row = cls(
            id=id,
            quantity=quantity,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
            product_availability=product_availability,
            product_expected_date=product_expected_date,
            price_per_unit=price_per_unit,
            price_per_unit_in_base_currency=price_per_unit_in_base_currency,
            total=total,
            total_in_base_currency=total_in_base_currency,
            cogs_value=cogs_value,
            attributes=attributes,
            batch_transactions=batch_transactions,
            serial_numbers=serial_numbers,
            linked_manufacturing_order_id=linked_manufacturing_order_id,
            conversion_rate=conversion_rate,
            conversion_date=conversion_date,
            created_at=created_at,
            updated_at=updated_at,
        )

        sales_order_row.additional_properties = d
        return sales_order_row

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
