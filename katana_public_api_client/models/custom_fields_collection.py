import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.custom_fields_collection_resource_type import (
    CustomFieldsCollectionResourceType,
)

if TYPE_CHECKING:
    from ..models.custom_field import CustomField


T = TypeVar("T", bound="CustomFieldsCollection")


@_attrs_define
class CustomFieldsCollection:
    """Collection of custom field definitions that can be applied to specific business objects for extended data capture

    Example:
        {'id': 5, 'name': 'Product Quality Specifications', 'resource_type': 'product', 'custom_fields': [{'id': 10,
            'name': 'quality_grade', 'field_type': 'select', 'label': 'Quality Grade', 'required': True, 'options': ['A',
            'B', 'C']}, {'id': 11, 'name': 'certification_date', 'field_type': 'date', 'label': 'Certification Date',
            'required': False}], 'created_at': '2024-01-08T10:00:00Z', 'updated_at': '2024-01-12T15:30:00Z'}

    Attributes:
        id (int): Unique identifier for the custom fields collection
        name (str): Display name of the custom fields collection for management and organization
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        resource_type (Union[Unset, CustomFieldsCollectionResourceType]): The type of business object this custom fields
            collection applies to
        custom_fields (Union[Unset, list['CustomField']]): Array of custom field definitions with their types,
            validation rules, and configuration
    """

    id: int
    name: str
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    resource_type: Unset | CustomFieldsCollectionResourceType = UNSET
    custom_fields: Unset | list["CustomField"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        resource_type: Unset | str = UNSET
        if not isinstance(self.resource_type, Unset):
            resource_type = self.resource_type.value

        custom_fields: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.custom_fields, Unset):
            custom_fields = []
            for custom_fields_item_data in self.custom_fields:
                custom_fields_item = custom_fields_item_data.to_dict()
                custom_fields.append(custom_fields_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if resource_type is not UNSET:
            field_dict["resource_type"] = resource_type
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field import CustomField

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        _resource_type = d.pop("resource_type", UNSET)
        resource_type: Unset | CustomFieldsCollectionResourceType
        if isinstance(_resource_type, Unset):
            resource_type = UNSET
        else:
            resource_type = CustomFieldsCollectionResourceType(_resource_type)

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = CustomField.from_dict(custom_fields_item_data)

            custom_fields.append(custom_fields_item)

        custom_fields_collection = cls(
            id=id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            resource_type=resource_type,
            custom_fields=custom_fields,
        )

        custom_fields_collection.additional_properties = d
        return custom_fields_collection

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
