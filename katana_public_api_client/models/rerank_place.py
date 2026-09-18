from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RerankPlace")


@_attrs_define
class RerankPlace:
    """Placement target for a rerank operation. Ranking is relative, mirroring drag-and-drop reordering - the reranked
    order is moved next to the target order.

        Example:
            {'before_id': 4}
    """

    before_id: int

    def to_dict(self) -> dict[str, Any]:
        before_id = self.before_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "before_id": before_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        before_id = d.pop("before_id")

        rerank_place = cls(
            before_id=before_id,
        )

        return rerank_place
