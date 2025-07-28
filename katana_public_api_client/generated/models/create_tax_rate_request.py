from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateTaxRateRequest")


@_attrs_define
class CreateTaxRateRequest:
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
