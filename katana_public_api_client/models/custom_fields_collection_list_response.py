from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_fields_collection import CustomFieldsCollection


T = TypeVar("T", bound="CustomFieldsCollectionListResponse")


@_attrs_define
class CustomFieldsCollectionListResponse:
    """List of custom field collections configured for extending business object data capture

    Example:
        {'data': [{'id': 5, 'name': 'Product Quality Specifications', 'resource_type': 'product', 'custom_fields':
            [{'id': 10, 'name': 'quality_grade', 'field_type': 'select', 'label': 'Quality Grade', 'required': True,
            'options': ['A', 'B', 'C']}, {'id': 11, 'name': 'certification_date', 'field_type': 'date', 'label':
            'Certification Date', 'required': False}], 'created_at': '2024-01-08T10:00:00Z', 'updated_at':
            '2024-01-12T15:30:00Z'}, {'id': 6, 'name': 'Customer Account Details', 'resource_type': 'customer',
            'custom_fields': [{'id': 12, 'name': 'credit_limit', 'field_type': 'number', 'label': 'Credit Limit',
            'required': True}, {'id': 13, 'name': 'payment_terms', 'field_type': 'select', 'label': 'Payment Terms',
            'required': True, 'options': ['Net 30', 'Net 60', 'COD']}], 'created_at': '2024-01-10T11:00:00Z', 'updated_at':
            '2024-01-14T09:15:00Z'}]}

    Attributes:
        data (Union[Unset, list['CustomFieldsCollection']]): Array of custom field collections with their field
            definitions and configuration
    """

    data: Unset | list["CustomFieldsCollection"] = UNSET
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
        from ..models.custom_fields_collection import CustomFieldsCollection

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = CustomFieldsCollection.from_dict(data_item_data)

            data.append(data_item)

        custom_fields_collection_list_response = cls(
            data=data,
        )

        custom_fields_collection_list_response.additional_properties = d
        return custom_fields_collection_list_response

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
