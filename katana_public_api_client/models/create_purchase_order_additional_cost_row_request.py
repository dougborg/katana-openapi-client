from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.cost_distribution_method import CostDistributionMethod

T = TypeVar("T", bound="CreatePurchaseOrderAdditionalCostRowRequest")


@_attrs_define
class CreatePurchaseOrderAdditionalCostRowRequest:
    """Request payload for adding additional costs (shipping, duties, handling fees) to a purchase order

    Example:
        {'additional_cost_id': 1, 'group_id': 1, 'tax_rate_id': 1, 'price': 125.0, 'distribution_method': 'BY_VALUE',
            'reference': 'Customs invoice #123'}
    """

    additional_cost_id: int
    group_id: int
    tax_rate_id: int
    price: float
    distribution_method: CostDistributionMethod | Unset = UNSET
    reference: str | Unset | None = UNSET

    def to_dict(self) -> dict[str, Any]:
        additional_cost_id = self.additional_cost_id

        group_id = self.group_id

        tax_rate_id = self.tax_rate_id

        price = self.price

        distribution_method: str | Unset = UNSET
        if not isinstance(self.distribution_method, Unset):
            distribution_method = self.distribution_method.value

        reference: str | Unset | None
        if isinstance(self.reference, Unset):
            reference = UNSET
        else:
            reference = self.reference

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
        if reference is not UNSET:
            field_dict["reference"] = reference

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_cost_id = d.pop("additional_cost_id")

        group_id = d.pop("group_id")

        tax_rate_id = d.pop("tax_rate_id")

        price = d.pop("price")

        _distribution_method = d.pop("distribution_method", UNSET)
        distribution_method: CostDistributionMethod | Unset
        if isinstance(_distribution_method, Unset):
            distribution_method = UNSET
        else:
            distribution_method = CostDistributionMethod(_distribution_method)

        def _parse_reference(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        reference = _parse_reference(d.pop("reference", UNSET))

        create_purchase_order_additional_cost_row_request = cls(
            additional_cost_id=additional_cost_id,
            group_id=group_id,
            tax_rate_id=tax_rate_id,
            price=price,
            distribution_method=distribution_method,
            reference=reference,
        )

        return create_purchase_order_additional_cost_row_request
