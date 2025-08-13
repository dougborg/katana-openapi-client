from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_operation_row import (
        ManufacturingOrderOperationRow,
    )


T = TypeVar("T", bound="ManufacturingOrderOperationRowListResponse")


@_attrs_define
class ManufacturingOrderOperationRowListResponse:
    """Response containing a list of manufacturing order operation rows with time tracking and operator assignments

    Example:
        {'data': [{'id': 1501, 'manufacturing_order_id': 1001, 'operation_id': 201, 'time': 45.5, 'total_actual_time':
            52.3, 'completed_by_operators': [{'id': 101, 'name': 'John Smith'}], 'created_at': '2023-10-15T09:00:00Z',
            'updated_at': '2023-10-15T10:30:00Z'}]}
    """

    data: Unset | list["ManufacturingOrderOperationRow"] = UNSET
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
        from ..models.manufacturing_order_operation_row import (
            ManufacturingOrderOperationRow,
        )

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = ManufacturingOrderOperationRow.from_dict(data_item_data)

            data.append(data_item)

        manufacturing_order_operation_row_list_response = cls(
            data=data,
        )

        manufacturing_order_operation_row_list_response.additional_properties = d
        return manufacturing_order_operation_row_list_response

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
