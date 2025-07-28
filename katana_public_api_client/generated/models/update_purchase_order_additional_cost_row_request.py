from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_purchase_order_additional_cost_row_request_distribution_method import (
    UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePurchaseOrderAdditionalCostRowRequest")


@_attrs_define
class UpdatePurchaseOrderAdditionalCostRowRequest:
    additional_cost_id: Unset | int = UNSET
    tax_rate_id: Unset | int = UNSET
    price: Unset | float = UNSET
    distribution_method: (
        Unset | UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        additional_cost_id = self.additional_cost_id

        tax_rate_id = self.tax_rate_id

        price = self.price

        distribution_method: Unset | str = UNSET
        if not isinstance(self.distribution_method, Unset):
            distribution_method = self.distribution_method.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if additional_cost_id is not UNSET:
            field_dict["additional_cost_id"] = additional_cost_id
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if price is not UNSET:
            field_dict["price"] = price
        if distribution_method is not UNSET:
            field_dict["distribution_method"] = distribution_method

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_cost_id = d.pop("additional_cost_id", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        price = d.pop("price", UNSET)

        _distribution_method = d.pop("distribution_method", UNSET)
        distribution_method: (
            Unset | UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod
        )
        if isinstance(_distribution_method, Unset):
            distribution_method = UNSET
        else:
            distribution_method = (
                UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod(
                    _distribution_method
                )
            )

        update_purchase_order_additional_cost_row_request = cls(
            additional_cost_id=additional_cost_id,
            tax_rate_id=tax_rate_id,
            price=price,
            distribution_method=distribution_method,
        )

        return update_purchase_order_additional_cost_row_request
