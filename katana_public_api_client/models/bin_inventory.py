from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="BinInventory")


@_attrs_define
class BinInventory:
    """Per-bin inventory position at the requested granularity. Quantities are decimal
    strings. A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes
    stock whose traceability on that axis is unset. Rows reaching zero across all
    three quantities are removed, so absence implies zero.
    """

    location_id: int | Unset = UNSET
    variant_id: int | Unset = UNSET
    bin_location_id: int | None | Unset = UNSET
    batch_id: int | None | Unset = UNSET
    serial_number_id: int | None | Unset = UNSET
    quantity_in_stock: str | Unset = UNSET
    quantity_committed: str | Unset = UNSET
    quantity_expected: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        variant_id = self.variant_id

        bin_location_id: int | None | Unset
        if isinstance(self.bin_location_id, Unset):
            bin_location_id = UNSET
        else:
            bin_location_id = self.bin_location_id

        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        serial_number_id: int | None | Unset
        if isinstance(self.serial_number_id, Unset):
            serial_number_id = UNSET
        else:
            serial_number_id = self.serial_number_id

        quantity_in_stock = self.quantity_in_stock

        quantity_committed = self.quantity_committed

        quantity_expected = self.quantity_expected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if bin_location_id is not UNSET:
            field_dict["bin_location_id"] = bin_location_id
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if serial_number_id is not UNSET:
            field_dict["serial_number_id"] = serial_number_id
        if quantity_in_stock is not UNSET:
            field_dict["quantity_in_stock"] = quantity_in_stock
        if quantity_committed is not UNSET:
            field_dict["quantity_committed"] = quantity_committed
        if quantity_expected is not UNSET:
            field_dict["quantity_expected"] = quantity_expected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        location_id = d.pop("location_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        def _parse_bin_location_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        bin_location_id = _parse_bin_location_id(d.pop("bin_location_id", UNSET))

        def _parse_batch_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_serial_number_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        serial_number_id = _parse_serial_number_id(d.pop("serial_number_id", UNSET))

        quantity_in_stock = d.pop("quantity_in_stock", UNSET)

        quantity_committed = d.pop("quantity_committed", UNSET)

        quantity_expected = d.pop("quantity_expected", UNSET)

        bin_inventory = cls(
            location_id=location_id,
            variant_id=variant_id,
            bin_location_id=bin_location_id,
            batch_id=batch_id,
            serial_number_id=serial_number_id,
            quantity_in_stock=quantity_in_stock,
            quantity_committed=quantity_committed,
            quantity_expected=quantity_expected,
        )

        bin_inventory.additional_properties = d
        return bin_inventory

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
