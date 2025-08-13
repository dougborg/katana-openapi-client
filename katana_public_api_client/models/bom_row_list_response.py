from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bom_row import BomRow


T = TypeVar("T", bound="BomRowListResponse")


@_attrs_define
class BomRowListResponse:
    """Response containing a list of BOM rows

    Example:
        {'data': [{'id': 501, 'product_variant_id': 2001, 'product_item_id': 3001, 'ingredient_variant_id': 2002,
            'quantity': 2.5, 'notes': 'Handle with care - fragile component', 'created_at': '2023-10-15T14:30:00Z',
            'updated_at': '2023-10-16T09:15:00Z'}, {'id': 502, 'product_variant_id': 2001, 'product_item_id': 3001,
            'ingredient_variant_id': 2003, 'quantity': 1.0, 'notes': 'Standard component', 'created_at':
            '2023-10-15T14:31:00Z', 'updated_at': '2023-10-15T14:31:00Z'}]}
    """

    data: Unset | list["BomRow"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bom_row import BomRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = BomRow.from_dict(data_item_data)

            data.append(data_item)

        bom_row_list_response = cls(
            data=data,
        )

        bom_row_list_response.additional_properties = d
        return bom_row_list_response

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
