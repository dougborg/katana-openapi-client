from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.create_purchase_order_additional_cost_row_request_distribution_method import (
    CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreatePurchaseOrderAdditionalCostRowRequest")


@_attrs_define
class CreatePurchaseOrderAdditionalCostRowRequest:
    additional_cost_id: int
    group_id: int
    tax_rate_id: int
    price: float
    distribution_method: (
        Unset | CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        additional_cost_id = self.additional_cost_id

        group_id = self.group_id

        tax_rate_id = self.tax_rate_id

        price = self.price

        distribution_method: Unset | str = UNSET
        if not isinstance(self.distribution_method, Unset):
            distribution_method = self.distribution_method.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "additional_cost_id": additional_cost_id,
                "group_id": group_id,
                "tax_rate_id": tax_rate_id,
                "price": price,
            }
        )
        if distribution_method is not UNSET:
            field_dict["distribution_method"] = distribution_method

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_cost_id = d.pop("additional_cost_id")

        group_id = d.pop("group_id")

        tax_rate_id = d.pop("tax_rate_id")

        price = d.pop("price")

        _distribution_method = d.pop("distribution_method", UNSET)
        distribution_method: (
            Unset | CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod
        )
        if isinstance(_distribution_method, Unset):
            distribution_method = UNSET
        else:
            distribution_method = (
                CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod(
                    _distribution_method
                )
            )

        create_purchase_order_additional_cost_row_request = cls(
            additional_cost_id=additional_cost_id,
            group_id=group_id,
            tax_rate_id=tax_rate_id,
            price=price,
            distribution_method=distribution_method,
        )

        return create_purchase_order_additional_cost_row_request
