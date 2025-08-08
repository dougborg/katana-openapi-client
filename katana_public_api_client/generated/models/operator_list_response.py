from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.operator import Operator


T = TypeVar("T", bound="OperatorListResponse")


@_attrs_define
class OperatorListResponse:
    """Response containing a list of manufacturing floor operators

    Example:
        {'data': [{'id': 2001, 'operator_id': 'OP-001', 'operator_name': 'Mike Rodriguez', 'working_area': 'Assembly
            Line A', 'resource_id': 301, 'created_at': '2024-01-10T07:00:00.000Z', 'updated_at': '2024-03-15T06:30:00.000Z',
            'deleted_at': None}, {'id': 2002, 'operator_id': 'OP-002', 'operator_name': 'Jennifer Kim', 'working_area':
            'Quality Control', 'resource_id': 302, 'created_at': '2024-01-12T08:00:00.000Z', 'updated_at':
            '2024-03-15T07:45:00.000Z', 'deleted_at': None}, {'id': 2003, 'operator_id': 'OP-003', 'operator_name': 'Carlos
            Mendez', 'working_area': 'Packaging Station', 'resource_id': 303, 'created_at': '2024-01-15T06:30:00.000Z',
            'updated_at': '2024-03-15T08:00:00.000Z', 'deleted_at': None}, {'id': 2004, 'operator_id': 'OP-004',
            'operator_name': 'Lisa Wang', 'working_area': 'Assembly Line B', 'resource_id': 304, 'created_at':
            '2024-02-01T07:30:00.000Z', 'updated_at': '2024-03-15T06:15:00.000Z', 'deleted_at': None}, {'id': 2005,
            'operator_id': 'OP-005', 'operator_name': 'Tom Peterson', 'working_area': 'Maintenance', 'resource_id': 305,
            'created_at': '2024-01-20T08:30:00.000Z', 'updated_at': '2024-03-10T15:00:00.000Z', 'deleted_at':
            '2024-03-10T15:00:00.000Z'}]}
    """

    data: Unset | list["Operator"] = UNSET
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
        from ..models.operator import Operator

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Operator.from_dict(data_item_data)

            data.append(data_item)

        operator_list_response = cls(
            data=data,
        )

        operator_list_response.additional_properties = d
        return operator_list_response

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
