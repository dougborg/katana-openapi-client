from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.additional_cost import AdditionalCost


T = TypeVar("T", bound="AdditionalCostListResponse")


@_attrs_define
class AdditionalCostListResponse:
    """Response containing a list of additional cost types for purchase orders and manufacturing orders

    Example:
        {'data': [{'id': 1, 'name': 'Shipping Cost', 'created_at': '2020-10-23T10:37:05.085Z', 'updated_at':
            '2020-10-23T10:37:05.085Z', 'deleted_at': None}, {'id': 2, 'name': 'Import Duty', 'created_at':
            '2020-10-23T10:37:05.085Z', 'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['AdditionalCost']]): Array of additional cost types that can be applied to orders
    """

    data: Unset | list["AdditionalCost"] = UNSET
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
        from ..models.additional_cost import AdditionalCost

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = AdditionalCost.from_dict(data_item_data)

            data.append(data_item)

        additional_cost_list_response = cls(
            data=data,
        )

        additional_cost_list_response.additional_properties = d
        return additional_cost_list_response

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
