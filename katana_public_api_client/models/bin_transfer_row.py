from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bin_transfer_traceability import BinTransferTraceability


T = TypeVar("T", bound="BinTransferRow")


@_attrs_define
class BinTransferRow:
    """Line item in a bin transfer — the variant, quantity, and source/target bins the
    stock moves between, with optional batch/serial traceability.
    """

    id: int
    bin_transfer_id: int
    variant_id: int
    quantity: str
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    location_id: int | Unset = UNSET
    source_bin_location_id: int | None | Unset = UNSET
    target_bin_location_id: int | None | Unset = UNSET
    traceability: list[BinTransferTraceability] | Unset = UNSET
    created_date: datetime.datetime | None | Unset = UNSET
    departed_at: datetime.datetime | None | Unset = UNSET
    arrived_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        bin_transfer_id = self.bin_transfer_id

        variant_id = self.variant_id

        quantity = self.quantity

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

        location_id = self.location_id

        source_bin_location_id: int | None | Unset
        if isinstance(self.source_bin_location_id, Unset):
            source_bin_location_id = UNSET
        else:
            source_bin_location_id = self.source_bin_location_id

        target_bin_location_id: int | None | Unset
        if isinstance(self.target_bin_location_id, Unset):
            target_bin_location_id = UNSET
        else:
            target_bin_location_id = self.target_bin_location_id

        traceability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.traceability, Unset):
            traceability = []
            for traceability_item_data in self.traceability:
                traceability_item = traceability_item_data.to_dict()
                traceability.append(traceability_item)

        created_date: None | str | Unset
        if isinstance(self.created_date, Unset):
            created_date = UNSET
        elif isinstance(self.created_date, datetime.datetime):
            created_date = self.created_date.isoformat()
        else:
            created_date = self.created_date

        departed_at: None | str | Unset
        if isinstance(self.departed_at, Unset):
            departed_at = UNSET
        elif isinstance(self.departed_at, datetime.datetime):
            departed_at = self.departed_at.isoformat()
        else:
            departed_at = self.departed_at

        arrived_at: None | str | Unset
        if isinstance(self.arrived_at, Unset):
            arrived_at = UNSET
        elif isinstance(self.arrived_at, datetime.datetime):
            arrived_at = self.arrived_at.isoformat()
        else:
            arrived_at = self.arrived_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bin_transfer_id": bin_transfer_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if source_bin_location_id is not UNSET:
            field_dict["source_bin_location_id"] = source_bin_location_id
        if target_bin_location_id is not UNSET:
            field_dict["target_bin_location_id"] = target_bin_location_id
        if traceability is not UNSET:
            field_dict["traceability"] = traceability
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if departed_at is not UNSET:
            field_dict["departed_at"] = departed_at
        if arrived_at is not UNSET:
            field_dict["arrived_at"] = arrived_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_transfer_traceability import BinTransferTraceability

        d = dict(src_dict)
        id = d.pop("id")

        bin_transfer_id = d.pop("bin_transfer_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = datetime.datetime.fromisoformat(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        location_id = d.pop("location_id", UNSET)

        def _parse_source_bin_location_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        source_bin_location_id = _parse_source_bin_location_id(
            d.pop("source_bin_location_id", UNSET)
        )

        def _parse_target_bin_location_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        target_bin_location_id = _parse_target_bin_location_id(
            d.pop("target_bin_location_id", UNSET)
        )

        _traceability = d.pop("traceability", UNSET)
        traceability: list[BinTransferTraceability] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = BinTransferTraceability.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        def _parse_created_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_date_type_0 = datetime.datetime.fromisoformat(data)

                return created_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_date = _parse_created_date(d.pop("created_date", UNSET))

        def _parse_departed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                departed_at_type_0 = datetime.datetime.fromisoformat(data)

                return departed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        departed_at = _parse_departed_at(d.pop("departed_at", UNSET))

        def _parse_arrived_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                arrived_at_type_0 = datetime.datetime.fromisoformat(data)

                return arrived_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        arrived_at = _parse_arrived_at(d.pop("arrived_at", UNSET))

        bin_transfer_row = cls(
            id=id,
            bin_transfer_id=bin_transfer_id,
            variant_id=variant_id,
            quantity=quantity,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            location_id=location_id,
            source_bin_location_id=source_bin_location_id,
            target_bin_location_id=target_bin_location_id,
            traceability=traceability,
            created_date=created_date,
            departed_at=departed_at,
            arrived_at=arrived_at,
        )

        bin_transfer_row.additional_properties = d
        return bin_transfer_row

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
