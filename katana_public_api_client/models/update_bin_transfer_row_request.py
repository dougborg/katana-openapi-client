from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bin_transfer_traceability_request import (
        BinTransferTraceabilityRequest,
    )


T = TypeVar("T", bound="UpdateBinTransferRowRequest")


@_attrs_define
class UpdateBinTransferRowRequest:
    """Request payload for updating a bin transfer row.

    Example:
        {'quantity': '5'}
    """

    variant_id: int | Unset = UNSET
    quantity: str | Unset = UNSET
    source_bin_location_id: int | None | Unset = UNSET
    target_bin_location_id: int | None | Unset = UNSET
    traceability: list[BinTransferTraceabilityRequest] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

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

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if source_bin_location_id is not UNSET:
            field_dict["source_bin_location_id"] = source_bin_location_id
        if target_bin_location_id is not UNSET:
            field_dict["target_bin_location_id"] = target_bin_location_id
        if traceability is not UNSET:
            field_dict["traceability"] = traceability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_transfer_traceability_request import (
            BinTransferTraceabilityRequest,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        quantity = d.pop("quantity", UNSET)

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
        traceability: list[BinTransferTraceabilityRequest] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = BinTransferTraceabilityRequest.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        update_bin_transfer_row_request = cls(
            variant_id=variant_id,
            quantity=quantity,
            source_bin_location_id=source_bin_location_id,
            target_bin_location_id=target_bin_location_id,
            traceability=traceability,
        )

        return update_bin_transfer_row_request
