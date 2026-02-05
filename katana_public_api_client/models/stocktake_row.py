from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="StocktakeRow")


@_attrs_define
class StocktakeRow:
    """Individual item record within a stocktake showing system vs actual quantities and variance"""

    id: int
    stocktake_id: int
    variant_id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    batch_id: int | None | Unset = UNSET
    in_stock_quantity: float | None | Unset = UNSET
    counted_quantity: float | None | Unset = UNSET
    discrepancy_quantity: float | None | Unset = UNSET
    notes: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stocktake_id = self.stocktake_id

        variant_id = self.variant_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        in_stock_quantity: float | None | Unset
        if isinstance(self.in_stock_quantity, Unset):
            in_stock_quantity = UNSET
        else:
            in_stock_quantity = self.in_stock_quantity

        counted_quantity: float | None | Unset
        if isinstance(self.counted_quantity, Unset):
            counted_quantity = UNSET
        else:
            counted_quantity = self.counted_quantity

        discrepancy_quantity: float | None | Unset
        if isinstance(self.discrepancy_quantity, Unset):
            discrepancy_quantity = UNSET
        else:
            discrepancy_quantity = self.discrepancy_quantity

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "stocktake_id": stocktake_id,
                "variant_id": variant_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if in_stock_quantity is not UNSET:
            field_dict["in_stock_quantity"] = in_stock_quantity
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity
        if discrepancy_quantity is not UNSET:
            field_dict["discrepancy_quantity"] = discrepancy_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        stocktake_id = d.pop("stocktake_id")

        variant_id = d.pop("variant_id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        def _parse_batch_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_in_stock_quantity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        in_stock_quantity = _parse_in_stock_quantity(d.pop("in_stock_quantity", UNSET))

        def _parse_counted_quantity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        counted_quantity = _parse_counted_quantity(d.pop("counted_quantity", UNSET))

        def _parse_discrepancy_quantity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        discrepancy_quantity = _parse_discrepancy_quantity(
            d.pop("discrepancy_quantity", UNSET)
        )

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        stocktake_row = cls(
            id=id,
            stocktake_id=stocktake_id,
            variant_id=variant_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            batch_id=batch_id,
            in_stock_quantity=in_stock_quantity,
            counted_quantity=counted_quantity,
            discrepancy_quantity=discrepancy_quantity,
            notes=notes,
        )

        stocktake_row.additional_properties = d
        return stocktake_row

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
