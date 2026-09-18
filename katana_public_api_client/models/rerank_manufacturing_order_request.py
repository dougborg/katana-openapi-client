from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.rerank_place import RerankPlace


T = TypeVar("T", bound="RerankManufacturingOrderRequest")


@_attrs_define
class RerankManufacturingOrderRequest:
    """Request payload for repositioning a manufacturing order in the production schedule, relative to another
    manufacturing order

        Example:
            {'order_ids': [1], 'place': {'before_id': 4}}
    """

    order_ids: list[int]
    place: RerankPlace

    def to_dict(self) -> dict[str, Any]:
        order_ids = self.order_ids

        place = self.place.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "order_ids": order_ids,
                "place": place,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.rerank_place import RerankPlace

        d = dict(src_dict)
        order_ids = cast(list[int], d.pop("order_ids"))

        place = RerankPlace.from_dict(d.pop("place"))

        rerank_manufacturing_order_request = cls(
            order_ids=order_ids,
            place=place,
        )

        return rerank_manufacturing_order_request
