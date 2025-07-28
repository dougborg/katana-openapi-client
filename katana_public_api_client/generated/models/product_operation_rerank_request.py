from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.product_operation_rerank_request_operation_ranks_item import (
        ProductOperationRerankRequestOperationRanksItem,
    )


T = TypeVar("T", bound="ProductOperationRerankRequest")


@_attrs_define
class ProductOperationRerankRequest:
    product_id: int
    operation_ranks: list["ProductOperationRerankRequestOperationRanksItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        product_id = self.product_id

        operation_ranks = []
        for operation_ranks_item_data in self.operation_ranks:
            operation_ranks_item = operation_ranks_item_data.to_dict()
            operation_ranks.append(operation_ranks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "product_id": product_id,
                "operation_ranks": operation_ranks,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.product_operation_rerank_request_operation_ranks_item import (
            ProductOperationRerankRequestOperationRanksItem,
        )

        d = dict(src_dict)
        product_id = d.pop("product_id")

        operation_ranks = []
        _operation_ranks = d.pop("operation_ranks")
        for operation_ranks_item_data in _operation_ranks:
            operation_ranks_item = (
                ProductOperationRerankRequestOperationRanksItem.from_dict(
                    operation_ranks_item_data
                )
            )

            operation_ranks.append(operation_ranks_item)

        product_operation_rerank_request = cls(
            product_id=product_id,
            operation_ranks=operation_ranks,
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
