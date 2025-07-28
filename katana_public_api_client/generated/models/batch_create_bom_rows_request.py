from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.create_bom_row_request import CreateBomRowRequest


T = TypeVar("T", bound="BatchCreateBomRowsRequest")


@_attrs_define
class BatchCreateBomRowsRequest:
    bom_rows: list["CreateBomRowRequest"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bom_rows = []
        for bom_rows_item_data in self.bom_rows:
            bom_rows_item = bom_rows_item_data.to_dict()
            bom_rows.append(bom_rows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bom_rows": bom_rows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_bom_row_request import CreateBomRowRequest

        d = dict(src_dict)
        bom_rows = []
        _bom_rows = d.pop("bom_rows")
        for bom_rows_item_data in _bom_rows:
            bom_rows_item = CreateBomRowRequest.from_dict(bom_rows_item_data)

            bom_rows.append(bom_rows_item)

        batch_create_bom_rows_request = cls(
            bom_rows=bom_rows,
        )

        batch_create_bom_rows_request.additional_properties = d
        return batch_create_bom_rows_request

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
