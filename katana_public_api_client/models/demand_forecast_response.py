from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.demand_forecast_period import DemandForecastPeriod


T = TypeVar("T", bound="DemandForecastResponse")


@_attrs_define
class DemandForecastResponse:
    """Demand forecast for a variant in a specific location with period breakdowns

    Example:
        {'variant_id': 1, 'location_id': 1, 'in_stock': '100', 'periods': [{'period_start': '2024-01-01T00:00:00.000Z',
            'period_end': '2024-01-06T23:59:59.999Z', 'in_stock': '125', 'expected': '50', 'committed': '25'}]}
    """

    variant_id: int
    location_id: int
    in_stock: str | Unset = UNSET
    periods: list[DemandForecastPeriod] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        in_stock = self.in_stock

        periods: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.periods, Unset):
            periods = []
            for periods_item_data in self.periods:
                periods_item = periods_item_data.to_dict()
                periods.append(periods_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
            }
        )
        if in_stock is not UNSET:
            field_dict["in_stock"] = in_stock
        if periods is not UNSET:
            field_dict["periods"] = periods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.demand_forecast_period import DemandForecastPeriod

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        in_stock = d.pop("in_stock", UNSET)

        _periods = d.pop("periods", UNSET)
        periods: list[DemandForecastPeriod] | Unset = UNSET
        if _periods is not UNSET:
            periods = []
            for periods_item_data in _periods:
                periods_item = DemandForecastPeriod.from_dict(periods_item_data)

                periods.append(periods_item)

        demand_forecast_response = cls(
            variant_id=variant_id,
            location_id=location_id,
            in_stock=in_stock,
            periods=periods,
        )

        demand_forecast_response.additional_properties = d
        return demand_forecast_response

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
