import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderAdditionalCostRow")


@_attrs_define
class PurchaseOrderAdditionalCostRow:
    """Additional cost line item within a purchase order, representing charges like shipping, duties, or handling fees

    Example:
        {'id': 201, 'additional_cost_id': 1, 'group_id': 1, 'name': 'International Shipping', 'distribution_method':
            'BY_VALUE', 'tax_rate_id': 1, 'tax_rate': 8.5, 'price': 125.0, 'price_in_base': 125.0, 'currency': 'USD',
            'currency_conversion_rate': 1.0, 'currency_conversion_rate_fix_date': '2024-01-28T09:15:00Z', 'created_at':
            '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z', 'deleted_at': None}

    Attributes:
        id (int): Unique identifier for this additional cost line item
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
        additional_cost_id (Union[Unset, int]): Unique identifier of the additional cost type (e.g., shipping, duty,
            handling)
        group_id (Union[Unset, int]): Group identifier for organizing related additional costs
        name (Union[Unset, str]): Name or description of the additional cost
        distribution_method (Union[Unset, str]): Method used for distributing this cost across purchase order items
        tax_rate_id (Union[Unset, int]): Tax rate identifier applied to this additional cost
        tax_rate (Union[Unset, float]): Tax rate percentage applied to this additional cost
        price (Union[Unset, float]): Amount of the additional cost in the purchase order currency
        price_in_base (Union[Unset, float]): Amount of the additional cost converted to base currency
        currency (Union[Unset, str]): Currency used for this additional cost
        currency_conversion_rate (Union[Unset, float]): Exchange rate used for currency conversion
        currency_conversion_rate_fix_date (Union[Unset, datetime.datetime]): Date when the currency conversion rate was
            fixed
    """

    id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_cost_id: Unset | int = UNSET
    group_id: Unset | int = UNSET
    name: Unset | str = UNSET
    distribution_method: Unset | str = UNSET
    tax_rate_id: Unset | int = UNSET
    tax_rate: Unset | float = UNSET
    price: Unset | float = UNSET
    price_in_base: Unset | float = UNSET
    currency: Unset | str = UNSET
    currency_conversion_rate: Unset | float = UNSET
    currency_conversion_rate_fix_date: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

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

        additional_cost_id = self.additional_cost_id

        group_id = self.group_id

        name = self.name

        distribution_method = self.distribution_method

        tax_rate_id = self.tax_rate_id

        tax_rate = self.tax_rate

        price = self.price

        price_in_base = self.price_in_base

        currency = self.currency

        currency_conversion_rate = self.currency_conversion_rate

        currency_conversion_rate_fix_date: Unset | str = UNSET
        if not isinstance(self.currency_conversion_rate_fix_date, Unset):
            currency_conversion_rate_fix_date = (
                self.currency_conversion_rate_fix_date.isoformat()
            )

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if additional_cost_id is not UNSET:
            field_dict["additional_cost_id"] = additional_cost_id
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if name is not UNSET:
            field_dict["name"] = name
        if distribution_method is not UNSET:
            field_dict["distribution_method"] = distribution_method
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if tax_rate is not UNSET:
            field_dict["tax_rate"] = tax_rate
        if price is not UNSET:
            field_dict["price"] = price
        if price_in_base is not UNSET:
            field_dict["price_in_base"] = price_in_base
        if currency is not UNSET:
            field_dict["currency"] = currency
        if currency_conversion_rate is not UNSET:
            field_dict["currency_conversion_rate"] = currency_conversion_rate
        if currency_conversion_rate_fix_date is not UNSET:
            field_dict["currency_conversion_rate_fix_date"] = (
                currency_conversion_rate_fix_date
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

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

        additional_cost_id = d.pop("additional_cost_id", UNSET)

        group_id = d.pop("group_id", UNSET)

        name = d.pop("name", UNSET)

        distribution_method = d.pop("distribution_method", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        tax_rate = d.pop("tax_rate", UNSET)

        price = d.pop("price", UNSET)

        price_in_base = d.pop("price_in_base", UNSET)

        currency = d.pop("currency", UNSET)

        currency_conversion_rate = d.pop("currency_conversion_rate", UNSET)

        _currency_conversion_rate_fix_date = d.pop(
            "currency_conversion_rate_fix_date", UNSET
        )
        currency_conversion_rate_fix_date: Unset | datetime.datetime
        if isinstance(_currency_conversion_rate_fix_date, Unset):
            currency_conversion_rate_fix_date = UNSET
        else:
            currency_conversion_rate_fix_date = isoparse(
                _currency_conversion_rate_fix_date
            )

        purchase_order_additional_cost_row = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            additional_cost_id=additional_cost_id,
            group_id=group_id,
            name=name,
            distribution_method=distribution_method,
            tax_rate_id=tax_rate_id,
            tax_rate=tax_rate,
            price=price,
            price_in_base=price_in_base,
            currency=currency,
            currency_conversion_rate=currency_conversion_rate,
            currency_conversion_rate_fix_date=currency_conversion_rate_fix_date,
        )

        purchase_order_additional_cost_row.additional_properties = d
        return purchase_order_additional_cost_row

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
