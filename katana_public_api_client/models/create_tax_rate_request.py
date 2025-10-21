from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateTaxRateRequest")


@_attrs_define
class CreateTaxRateRequest:
    """Request payload for creating a new tax rate to be applied to sales and purchase orders for financial compliance

    Example:
        {'name': 'VAT 20%', 'rate': 20.0}

    Attributes:
        rate (float): Tax rate as a percentage (e.g., 20.5 for 20.5%)
        name (Union[Unset, str]): Descriptive name for the tax rate (e.g., "VAT 20%", "Sales Tax", "GST")
    """

    rate: float
    name: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        rate = self.rate

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "rate": rate,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rate = d.pop("rate")

        name = d.pop("name", UNSET)

        create_tax_rate_request = cls(
            rate=rate,
            name=name,
        )

        return create_tax_rate_request
