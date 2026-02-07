from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="CreateDemandForecastRequestPeriodsItem")


@_attrs_define
class CreateDemandForecastRequestPeriodsItem:
    period_start: datetime.datetime
    period_end: datetime.datetime
    committed: str

    def to_dict(self) -> dict[str, Any]:
        period_start = self.period_start.isoformat()

        period_end = self.period_end.isoformat()

        committed = self.committed

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "period_start": period_start,
                "period_end": period_end,
                "committed": committed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        period_start = isoparse(d.pop("period_start"))

        period_end = isoparse(d.pop("period_end"))

        committed = d.pop("committed")

        create_demand_forecast_request_periods_item = cls(
            period_start=period_start,
            period_end=period_end,
            committed=committed,
        )

        return create_demand_forecast_request_periods_item
