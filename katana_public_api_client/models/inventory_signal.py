from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.inventory_signal_lead_time_source import InventorySignalLeadTimeSource

T = TypeVar("T", bound="InventorySignal")


@_attrs_define
class InventorySignal:
    """Replenishment signal for a single variant, summed across all locations. Derived nightly from the last 30 days of
    demand.

        Example:
            {'variant_id': 1, 'avg_daily_demand_30d': '3.50000000000000000000', 'reorder_point': '49.00000000000000000000',
                'days_of_stock_left': 12, 'stock_risk': 1, 'in_stock': '42.00000000000000000000', 'committed':
                '0.00000000000000000000', 'safety_stock_breach_at': '2026-08-24T00:00:00.000Z',
                'expected_before_safety_stock_breach': '30.00000000000000000000', 'safety_stock': '0.00000000000000000000',
                'lead_time_used': 14, 'lead_time_source': 'sku', 'demand_calculated_at': '2026-08-12T07:00:00.000Z'}
    """

    variant_id: int | Unset = UNSET
    avg_daily_demand_30d: str | Unset = UNSET
    reorder_point: str | Unset | None = UNSET
    days_of_stock_left: int | Unset | None = UNSET
    stock_risk: int | Unset | None = UNSET
    in_stock: str | Unset = UNSET
    committed: str | Unset = UNSET
    safety_stock_breach_at: datetime.datetime | Unset | None = UNSET
    expected_before_safety_stock_breach: str | Unset | None = UNSET
    safety_stock: str | Unset = UNSET
    lead_time_used: int | Unset = UNSET
    lead_time_source: InventorySignalLeadTimeSource | Unset = UNSET
    demand_calculated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        avg_daily_demand_30d = self.avg_daily_demand_30d

        reorder_point: str | Unset | None
        if isinstance(self.reorder_point, Unset):
            reorder_point = UNSET
        else:
            reorder_point = self.reorder_point

        days_of_stock_left: int | Unset | None
        if isinstance(self.days_of_stock_left, Unset):
            days_of_stock_left = UNSET
        else:
            days_of_stock_left = self.days_of_stock_left

        stock_risk: int | Unset | None
        if isinstance(self.stock_risk, Unset):
            stock_risk = UNSET
        else:
            stock_risk = self.stock_risk

        in_stock = self.in_stock

        committed = self.committed

        safety_stock_breach_at: str | Unset | None
        if isinstance(self.safety_stock_breach_at, Unset):
            safety_stock_breach_at = UNSET
        elif isinstance(self.safety_stock_breach_at, datetime.datetime):
            safety_stock_breach_at = self.safety_stock_breach_at.isoformat()
        else:
            safety_stock_breach_at = self.safety_stock_breach_at

        expected_before_safety_stock_breach: str | Unset | None
        if isinstance(self.expected_before_safety_stock_breach, Unset):
            expected_before_safety_stock_breach = UNSET
        else:
            expected_before_safety_stock_breach = (
                self.expected_before_safety_stock_breach
            )

        safety_stock = self.safety_stock

        lead_time_used = self.lead_time_used

        lead_time_source: str | Unset = UNSET
        if not isinstance(self.lead_time_source, Unset):
            lead_time_source = self.lead_time_source.value

        demand_calculated_at: str | Unset = UNSET
        if not isinstance(self.demand_calculated_at, Unset):
            demand_calculated_at = self.demand_calculated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if avg_daily_demand_30d is not UNSET:
            field_dict["avg_daily_demand_30d"] = avg_daily_demand_30d
        if reorder_point is not UNSET:
            field_dict["reorder_point"] = reorder_point
        if days_of_stock_left is not UNSET:
            field_dict["days_of_stock_left"] = days_of_stock_left
        if stock_risk is not UNSET:
            field_dict["stock_risk"] = stock_risk
        if in_stock is not UNSET:
            field_dict["in_stock"] = in_stock
        if committed is not UNSET:
            field_dict["committed"] = committed
        if safety_stock_breach_at is not UNSET:
            field_dict["safety_stock_breach_at"] = safety_stock_breach_at
        if expected_before_safety_stock_breach is not UNSET:
            field_dict["expected_before_safety_stock_breach"] = (
                expected_before_safety_stock_breach
            )
        if safety_stock is not UNSET:
            field_dict["safety_stock"] = safety_stock
        if lead_time_used is not UNSET:
            field_dict["lead_time_used"] = lead_time_used
        if lead_time_source is not UNSET:
            field_dict["lead_time_source"] = lead_time_source
        if demand_calculated_at is not UNSET:
            field_dict["demand_calculated_at"] = demand_calculated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        avg_daily_demand_30d = d.pop("avg_daily_demand_30d", UNSET)

        def _parse_reorder_point(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        reorder_point = _parse_reorder_point(d.pop("reorder_point", UNSET))

        def _parse_days_of_stock_left(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        days_of_stock_left = _parse_days_of_stock_left(
            d.pop("days_of_stock_left", UNSET)
        )

        def _parse_stock_risk(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        stock_risk = _parse_stock_risk(d.pop("stock_risk", UNSET))

        in_stock = d.pop("in_stock", UNSET)

        committed = d.pop("committed", UNSET)

        def _parse_safety_stock_breach_at(
            data: object,
        ) -> datetime.datetime | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                safety_stock_breach_at_type_0 = datetime.datetime.fromisoformat(data)

                return safety_stock_breach_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | Unset | None, data)

        safety_stock_breach_at = _parse_safety_stock_breach_at(
            d.pop("safety_stock_breach_at", UNSET)
        )

        def _parse_expected_before_safety_stock_breach(
            data: object,
        ) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        expected_before_safety_stock_breach = (
            _parse_expected_before_safety_stock_breach(
                d.pop("expected_before_safety_stock_breach", UNSET)
            )
        )

        safety_stock = d.pop("safety_stock", UNSET)

        lead_time_used = d.pop("lead_time_used", UNSET)

        _lead_time_source = d.pop("lead_time_source", UNSET)
        lead_time_source: InventorySignalLeadTimeSource | Unset
        if isinstance(_lead_time_source, Unset):
            lead_time_source = UNSET
        else:
            lead_time_source = InventorySignalLeadTimeSource(_lead_time_source)

        _demand_calculated_at = d.pop("demand_calculated_at", UNSET)
        demand_calculated_at: datetime.datetime | Unset
        if isinstance(_demand_calculated_at, Unset):
            demand_calculated_at = UNSET
        else:
            demand_calculated_at = datetime.datetime.fromisoformat(
                _demand_calculated_at
            )

        inventory_signal = cls(
            variant_id=variant_id,
            avg_daily_demand_30d=avg_daily_demand_30d,
            reorder_point=reorder_point,
            days_of_stock_left=days_of_stock_left,
            stock_risk=stock_risk,
            in_stock=in_stock,
            committed=committed,
            safety_stock_breach_at=safety_stock_breach_at,
            expected_before_safety_stock_breach=expected_before_safety_stock_breach,
            safety_stock=safety_stock,
            lead_time_used=lead_time_used,
            lead_time_source=lead_time_source,
            demand_calculated_at=demand_calculated_at,
        )

        inventory_signal.additional_properties = d
        return inventory_signal

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
