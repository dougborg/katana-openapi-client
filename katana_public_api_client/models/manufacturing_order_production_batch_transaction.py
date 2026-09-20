from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ManufacturingOrderProductionBatchTransaction")


@_attrs_define
class ManufacturingOrderProductionBatchTransaction:
    """Batch allocation for a manufacturing order production run.

    Deliberately **not** the shared ``BatchTransaction``: this endpoint
    takes the batch alone. The produced amount is already given by
    ``completed_quantity`` on the request body, so a per-batch
    ``quantity`` would be redundant — and upstream's
    ``CompletePartiallyBatchDto`` sets ``additionalProperties: false``,
    so sending one is rejected with 422 (verified against the live API
    2026-09-18, #1042).
    """

    batch_id: int

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "batch_id": batch_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id")

        manufacturing_order_production_batch_transaction = cls(
            batch_id=batch_id,
        )

        return manufacturing_order_production_batch_transaction
