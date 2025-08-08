import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.purchase_order_additional_cost_row_distribution_method import (
    PurchaseOrderAdditionalCostRowDistributionMethod,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderAdditionalCostRow")


@_attrs_define
class PurchaseOrderAdditionalCostRow:
    """Additional costs associated with a purchase order such as shipping, duties, handling fees, or other charges that are
    not part of the base product cost
    """

    id: int
    name: str
    price: float
    currency: str
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_cost_id: Unset | int = UNSET
    group_id: Unset | int = UNSET
    distribution_method: Unset | PurchaseOrderAdditionalCostRowDistributionMethod = (
        UNSET
    )
    tax_rate_id: Unset | int = UNSET
    tax_rate: Unset | float = UNSET
    price_in_base: Unset | float = UNSET
    currency_conversion_rate: Unset | float = UNSET
    currency_conversion_rate_fix_date: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        price = self.price

        currency = self.currency

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

        distribution_method: Unset | str = UNSET
        if not isinstance(self.distribution_method, Unset):
            distribution_method = self.distribution_method.value

        tax_rate_id = self.tax_rate_id

        tax_rate = self.tax_rate

        price_in_base = self.price_in_base

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
                "name": name,
                "price": price,
                "currency": currency,
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
        if distribution_method is not UNSET:
            field_dict["distribution_method"] = distribution_method
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if tax_rate is not UNSET:
            field_dict["tax_rate"] = tax_rate
        if price_in_base is not UNSET:
            field_dict["price_in_base"] = price_in_base
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

        name = d.pop("name")

        price = d.pop("price")

        currency = d.pop("currency")

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

        _distribution_method = d.pop("distribution_method", UNSET)
        distribution_method: Unset | PurchaseOrderAdditionalCostRowDistributionMethod
        if isinstance(_distribution_method, Unset):
            distribution_method = UNSET
        else:
            distribution_method = PurchaseOrderAdditionalCostRowDistributionMethod(
                _distribution_method
            )

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        tax_rate = d.pop("tax_rate", UNSET)

        price_in_base = d.pop("price_in_base", UNSET)

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
            name=name,
            price=price,
            currency=currency,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            additional_cost_id=additional_cost_id,
            group_id=group_id,
            distribution_method=distribution_method,
            tax_rate_id=tax_rate_id,
            tax_rate=tax_rate,
            price_in_base=price_in_base,
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
