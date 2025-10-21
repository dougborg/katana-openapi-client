from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="ProductOperationRerankRequest")


@_attrs_define
class ProductOperationRerankRequest:
    """Request payload for reordering product operations within a manufacturing workflow to optimize production sequence

    Example:
        {'rank_product_operation_id': 501, 'preceeding_product_operation_id': 499, 'should_group': True}

    Attributes:
        rank_product_operation_id (int): ID of the product operation to be reordered
        preceeding_product_operation_id (Union[Unset, int]): ID of the operation that should precede the operation being
            moved
        should_group (Union[Unset, bool]): Whether operations should be grouped together in the sequence
    """

    rank_product_operation_id: int
    preceeding_product_operation_id: Unset | int = UNSET
    should_group: Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rank_product_operation_id = self.rank_product_operation_id

        preceeding_product_operation_id = self.preceeding_product_operation_id

        should_group = self.should_group

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "rank_product_operation_id": rank_product_operation_id,
            }
        )
        if preceeding_product_operation_id is not UNSET:
            field_dict["preceeding_product_operation_id"] = (
                preceeding_product_operation_id
            )
        if should_group is not UNSET:
            field_dict["should_group"] = should_group

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rank_product_operation_id = d.pop("rank_product_operation_id")

        preceeding_product_operation_id = d.pop(
            "preceeding_product_operation_id", UNSET
        )

        should_group = d.pop("should_group", UNSET)

        product_operation_rerank_request = cls(
            rank_product_operation_id=rank_product_operation_id,
            preceeding_product_operation_id=preceeding_product_operation_id,
            should_group=should_group,
        )

        product_operation_rerank_request.additional_properties = d
        return product_operation_rerank_request

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
