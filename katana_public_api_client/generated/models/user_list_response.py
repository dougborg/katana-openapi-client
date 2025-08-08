from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="UserListResponse")


@_attrs_define
class UserListResponse:
    """Response containing a list of system users with their roles and access levels

    Example:
        {'data': [{'id': 1001, 'first_name': 'Sarah', 'last_name': 'Johnson', 'email':
            'sarah.johnson@acmemanufacturing.com', 'role': 'manager', 'status': 'active', 'last_login_at':
            '2024-03-15T08:30:00.000Z', 'created_at': '2024-01-15T10:00:00.000Z', 'updated_at': '2024-03-15T08:30:00.000Z'},
            {'id': 1002, 'first_name': 'David', 'last_name': 'Chen', 'email': 'david.chen@acmemanufacturing.com', 'role':
            'admin', 'status': 'active', 'last_login_at': '2024-03-15T09:15:00.000Z', 'created_at':
            '2024-01-10T08:00:00.000Z', 'updated_at': '2024-03-15T09:15:00.000Z'}, {'id': 1003, 'first_name': 'Maria',
            'last_name': 'Garcia', 'email': 'maria.garcia@acmemanufacturing.com', 'role': 'operator', 'status': 'active',
            'last_login_at': '2024-03-15T06:00:00.000Z', 'created_at': '2024-02-01T07:00:00.000Z', 'updated_at':
            '2024-03-15T06:00:00.000Z'}, {'id': 1004, 'first_name': 'Robert', 'last_name': 'Thompson', 'email':
            'robert.thompson@acmemanufacturing.com', 'role': 'accountant', 'status': 'active', 'last_login_at':
            '2024-03-14T16:45:00.000Z', 'created_at': '2024-01-20T10:30:00.000Z', 'updated_at':
            '2024-03-14T16:45:00.000Z'}]}
    """

    data: Unset | list["User"] = UNSET
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
        from ..models.user import User

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = User.from_dict(data_item_data)

            data.append(data_item)

        user_list_response = cls(
            data=data,
        )

        user_list_response.additional_properties = d
        return user_list_response

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
