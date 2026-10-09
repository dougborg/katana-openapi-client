from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.rerank_place_position import RerankPlacePosition

T = TypeVar("T", bound="RerankPlace")


@_attrs_define
class RerankPlace:
    """Exact placement for reranked orders. Supply exactly one of before_id, after_id, or position.

    Example:
        {'before_id': 4}
    """

    after_id: int | Unset = UNSET
    position: RerankPlacePosition | Unset = UNSET
    before_id: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        after_id = self.after_id

        position: str | Unset = UNSET
        if not isinstance(self.position, Unset):
            position = self.position.value

        before_id = self.before_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if after_id is not UNSET:
            field_dict["after_id"] = after_id
        if position is not UNSET:
            field_dict["position"] = position
        if before_id is not UNSET:
            field_dict["before_id"] = before_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        after_id = d.pop("after_id", UNSET)

        _position = d.pop("position", UNSET)
        position: RerankPlacePosition | Unset
        if isinstance(_position, Unset):
            position = UNSET
        else:
            position = RerankPlacePosition(_position)

        before_id = d.pop("before_id", UNSET)

        rerank_place = cls(
            after_id=after_id,
            position=position,
            before_id=before_id,
        )

        return rerank_place
