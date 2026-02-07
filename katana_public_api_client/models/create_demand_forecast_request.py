from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.create_demand_forecast_request_periods_item import (
        CreateDemandForecastRequestPeriodsItem,
    )


T = TypeVar("T", bound="CreateDemandForecastRequest")


@_attrs_define
class CreateDemandForecastRequest:
    """Request payload for adding planned demand forecast periods for a variant in a location

    Example:
        {'variant_id': 1, 'location_id': 1, 'periods': [{'period_start': '2024-01-01T00:00:00.000Z', 'period_end':
            '2024-01-06T23:59:59.999Z', 'committed': '25'}]}
    """

    variant_id: int
    location_id: int
    periods: list[CreateDemandForecastRequestPeriodsItem]

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        periods = []
        for periods_item_data in self.periods:
            periods_item = periods_item_data.to_dict()
            periods.append(periods_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "periods": periods,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_demand_forecast_request_periods_item import (
            CreateDemandForecastRequestPeriodsItem,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        periods = []
        _periods = d.pop("periods")
        for periods_item_data in _periods:
            periods_item = CreateDemandForecastRequestPeriodsItem.from_dict(
                periods_item_data
            )

            periods.append(periods_item)

        create_demand_forecast_request = cls(
            variant_id=variant_id,
            location_id=location_id,
            periods=periods,
        )

        return create_demand_forecast_request
