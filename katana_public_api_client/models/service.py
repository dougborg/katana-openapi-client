import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.service_type import ServiceType

if TYPE_CHECKING:
    from ..models.service_variant import ServiceVariant


T = TypeVar("T", bound="Service")


@_attrs_define
class Service:
    """External service that can be used as part of manufacturing operations or business processes

    Example:
        {'id': 1, 'name': 'Service name', 'uom': 'pcs', 'category_name': 'Service', 'is_sellable': True, 'type':
            'service', 'custom_field_collection_id': 1, 'additional_info': 'additional info', 'created_at':
            '2020-10-23T10:37:05.085Z', 'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None, 'archived_at':
            '2020-10-20T10:37:05.085Z', 'variants': [{'id': 1, 'sku': 'S-2486', 'sales_price': None, 'default_cost': None,
            'service_id': 1, 'type': 'service', 'created_at': '2020-10-23T10:37:05.085Z', 'updated_at':
            '2020-10-23T10:37:05.085Z', 'deleted_at': None, 'custom_fields': [{'field_name': 'Power level', 'field_value':
            'Strong'}]}]}

    Attributes:
        id (int): Unique identifier
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        archived_at (Union[None, Unset, str]): Nullable archive timestamp
        deleted_at (Union[None, Unset, str]): Nullable deletion timestamp
        name (Union[Unset, str]): The service's unique name
        uom (Union[Unset, str]): The unit used to measure the quantity of the service (e.g. pcs, hours)
        category_name (Union[Unset, str]): A string used to group similar items for better organization and analysis
        is_sellable (Union[Unset, bool]): Sellable services can be added to Quotes and Sales orders
        type_ (Union[Unset, ServiceType]): Indicating the item type. Service objects are of type "service"
        additional_info (Union[Unset, str]): A string attached to the object to add any internal comments, links to
            external files, additional instructions, etc.
        custom_field_collection_id (Union[None, Unset, int]): ID of the custom field collection associated with this
            service
        variants (Union[Unset, list['ServiceVariant']]): An array of service variant objects
    """

    id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    archived_at: None | Unset | str = UNSET
    deleted_at: None | Unset | str = UNSET
    name: Unset | str = UNSET
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    is_sellable: Unset | bool = UNSET
    type_: Unset | ServiceType = UNSET
    additional_info: Unset | str = UNSET
    custom_field_collection_id: None | Unset | int = UNSET
    variants: Unset | list["ServiceVariant"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        archived_at: None | Unset | str
        if isinstance(self.archived_at, Unset):
            archived_at = UNSET
        else:
            archived_at = self.archived_at

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = self.deleted_at

        name = self.name

        uom = self.uom

        category_name = self.category_name

        is_sellable = self.is_sellable

        type_: Unset | str = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        additional_info = self.additional_info

        custom_field_collection_id: None | Unset | int
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

        variants: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.variants, Unset):
            variants = []
            for variants_item_data in self.variants:
                variants_item = variants_item_data.to_dict()
                variants.append(variants_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if archived_at is not UNSET:
            field_dict["archived_at"] = archived_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if name is not UNSET:
            field_dict["name"] = name
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if type_ is not UNSET:
            field_dict["type"] = type_
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id
        if variants is not UNSET:
            field_dict["variants"] = variants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_variant import ServiceVariant

        d = dict(src_dict)
        id = d.pop("id")

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

        def _parse_archived_at(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        archived_at = _parse_archived_at(d.pop("archived_at", UNSET))

        def _parse_deleted_at(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        name = d.pop("name", UNSET)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Unset | ServiceType
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ServiceType(_type_)

        additional_info = d.pop("additional_info", UNSET)

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        variants = []
        _variants = d.pop("variants", UNSET)
        for variants_item_data in _variants or []:
            variants_item = ServiceVariant.from_dict(variants_item_data)

            variants.append(variants_item)

        service = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            archived_at=archived_at,
            deleted_at=deleted_at,
            name=name,
            uom=uom,
            category_name=category_name,
            is_sellable=is_sellable,
            type_=type_,
            additional_info=additional_info,
            custom_field_collection_id=custom_field_collection_id,
            variants=variants,
        )

        service.additional_properties = d
        return service

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
