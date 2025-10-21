from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="UserListResponse")


@_attrs_define
class UserListResponse:
    """List of system users with their account information and role assignments

    Example:
        {'data': [{'id': 42, 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.johnson@company.com',
            'role': 'production_manager', 'status': 'active', 'last_login_at': '2024-01-15T14:30:00Z', 'created_at':
            '2024-01-10T09:00:00Z', 'updated_at': '2024-01-15T14:30:00Z'}, {'id': 43, 'first_name': 'Mike', 'last_name':
            'Chen', 'email': 'mike.chen@company.com', 'role': 'inventory_coordinator', 'status': 'active', 'last_login_at':
            '2024-01-15T10:15:00Z', 'created_at': '2024-01-08T11:00:00Z', 'updated_at': '2024-01-15T10:15:00Z'}]}

    Attributes:
        data (Union[Unset, list['User']]): Array of user accounts with authentication and permission details
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
