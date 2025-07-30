import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_row_batch_transactions_item import (
        PurchaseOrderRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="PurchaseOrderRow")


@_attrs_define
class PurchaseOrderRow:
    id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    variant_id: Unset | int = UNSET
    tax_rate_id: Unset | int = UNSET
    price_per_unit: Unset | float = UNSET
    price_per_unit_in_base_currency: Unset | float = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    purchase_uom: Unset | str = UNSET
    currency: Unset | str = UNSET
    conversion_rate: None | Unset | float = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    conversion_date: None | Unset | datetime.datetime = UNSET
    received_date: None | Unset | datetime.datetime = UNSET
    arrival_date: None | Unset | datetime.datetime = UNSET
    batch_transactions: Unset | list["PurchaseOrderRowBatchTransactionsItem"] = UNSET
    purchase_order_id: Unset | int = UNSET
    landed_cost: Unset | float | str = UNSET
    group_id: Unset | int = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        quantity = self.quantity

        variant_id = self.variant_id

        tax_rate_id = self.tax_rate_id

        price_per_unit = self.price_per_unit

        price_per_unit_in_base_currency = self.price_per_unit_in_base_currency

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        currency = self.currency

        conversion_rate: None | Unset | float
        if isinstance(self.conversion_rate, Unset):
            conversion_rate = UNSET
        else:
            conversion_rate = self.conversion_rate

        total = self.total

        total_in_base_currency = self.total_in_base_currency

        conversion_date: None | Unset | str
        if isinstance(self.conversion_date, Unset):
            conversion_date = UNSET
        elif isinstance(self.conversion_date, datetime.datetime):
            conversion_date = self.conversion_date.isoformat()
        else:
            conversion_date = self.conversion_date

        received_date: None | Unset | str
        if isinstance(self.received_date, Unset):
            received_date = UNSET
        elif isinstance(self.received_date, datetime.datetime):
            received_date = self.received_date.isoformat()
        else:
            received_date = self.received_date

        arrival_date: None | Unset | str
        if isinstance(self.arrival_date, Unset):
            arrival_date = UNSET
        elif isinstance(self.arrival_date, datetime.datetime):
            arrival_date = self.arrival_date.isoformat()
        else:
            arrival_date = self.arrival_date

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        purchase_order_id = self.purchase_order_id

        landed_cost: Unset | float | str
        if isinstance(self.landed_cost, Unset):
            landed_cost = UNSET
        else:
            landed_cost = self.landed_cost

        group_id = self.group_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if price_per_unit_in_base_currency is not UNSET:
            field_dict["price_per_unit_in_base_currency"] = (
                price_per_unit_in_base_currency
            )
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if currency is not UNSET:
            field_dict["currency"] = currency
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if total is not UNSET:
            field_dict["total"] = total
        if total_in_base_currency is not UNSET:
            field_dict["total_in_base_currency"] = total_in_base_currency
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if received_date is not UNSET:
            field_dict["received_date"] = received_date
        if arrival_date is not UNSET:
            field_dict["arrival_date"] = arrival_date
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if purchase_order_id is not UNSET:
            field_dict["purchase_order_id"] = purchase_order_id
        if landed_cost is not UNSET:
            field_dict["landed_cost"] = landed_cost
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_row_batch_transactions_item import (
            PurchaseOrderRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        quantity = d.pop("quantity", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        price_per_unit = d.pop("price_per_unit", UNSET)

        price_per_unit_in_base_currency = d.pop(
            "price_per_unit_in_base_currency", UNSET
        )

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        currency = d.pop("currency", UNSET)

        def _parse_conversion_rate(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        conversion_rate = _parse_conversion_rate(d.pop("conversion_rate", UNSET))

        total = d.pop("total", UNSET)

        total_in_base_currency = d.pop("total_in_base_currency", UNSET)

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

        def _parse_received_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                received_date_type_0 = isoparse(data)

                return received_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        received_date = _parse_received_date(d.pop("received_date", UNSET))

        def _parse_arrival_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                arrival_date_type_0 = isoparse(data)

                return arrival_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        arrival_date = _parse_arrival_date(d.pop("arrival_date", UNSET))

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = PurchaseOrderRowBatchTransactionsItem.from_dict(
                batch_transactions_item_data
            )

            batch_transactions.append(batch_transactions_item)

        purchase_order_id = d.pop("purchase_order_id", UNSET)

        def _parse_landed_cost(data: object) -> Unset | float | str:
            if isinstance(data, Unset):
                return data
            return cast(Unset | float | str, data)

        landed_cost = _parse_landed_cost(d.pop("landed_cost", UNSET))

        group_id = d.pop("group_id", UNSET)

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        purchase_order_row = cls(
            id=id,
            quantity=quantity,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            price_per_unit=price_per_unit,
            price_per_unit_in_base_currency=price_per_unit_in_base_currency,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
            currency=currency,
            conversion_rate=conversion_rate,
            total=total,
            total_in_base_currency=total_in_base_currency,
            conversion_date=conversion_date,
            received_date=received_date,
            arrival_date=arrival_date,
            batch_transactions=batch_transactions,
            purchase_order_id=purchase_order_id,
            landed_cost=landed_cost,
            group_id=group_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        purchase_order_row.additional_properties = d
        return purchase_order_row

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
