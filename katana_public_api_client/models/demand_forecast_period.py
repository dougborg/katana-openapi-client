from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="DemandForecastPeriod")


@_attrs_define
class DemandForecastPeriod:
    """A single demand forecast period with stock and demand quantities

    Example:
        {'period_start': '2024-01-01T00:00:00.000Z', 'period_end': '2024-01-06T23:59:59.999Z', 'in_stock': '125',
            'expected': '50', 'committed': '25'}
    """

    period_start: datetime.datetime
    period_end: datetime.datetime
    in_stock: str | Unset = UNSET
    expected: str | Unset = UNSET
    committed: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        period_start = self.period_start.isoformat()

        period_end = self.period_end.isoformat()

        in_stock = self.in_stock

        expected = self.expected

        committed = self.committed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "period_start": period_start,
                "period_end": period_end,
            }
        )
        if in_stock is not UNSET:
            field_dict["in_stock"] = in_stock
        if expected is not UNSET:
            field_dict["expected"] = expected
        if committed is not UNSET:
            field_dict["committed"] = committed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        period_start = isoparse(d.pop("period_start"))

        period_end = isoparse(d.pop("period_end"))

        in_stock = d.pop("in_stock", UNSET)

        expected = d.pop("expected", UNSET)

        committed = d.pop("committed", UNSET)

        demand_forecast_period = cls(
            period_start=period_start,
            period_end=period_end,
            in_stock=in_stock,
            expected=expected,
            committed=committed,
        )

        demand_forecast_period.additional_properties = d
        return demand_forecast_period

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
