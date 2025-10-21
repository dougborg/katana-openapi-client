import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.service_variant_type import ServiceVariantType

if TYPE_CHECKING:
    from ..models.service_variant_custom_fields_item import (
        ServiceVariantCustomFieldsItem,
    )


T = TypeVar("T", bound="ServiceVariant")


@_attrs_define
class ServiceVariant:
    """Service variant with unique pricing and configuration for external services

    Example:
        {'id': 4001, 'sku': 'ASSM-001', 'sales_price': 75.0, 'default_cost': 50.0, 'service_id': 401, 'type': 'service',
            'custom_fields': [{'field_name': 'Skill Level', 'field_value': 'Expert'}, {'field_name': 'Duration',
            'field_value': '2 hours'}], 'created_at': '2024-01-15T08:00:00.000Z', 'updated_at': '2024-08-20T14:45:00.000Z',
            'deleted_at': None}

    Attributes:
        id (int): Unique identifier
        sku (str): A unique service code
        service_id (int): ID of the service this variant belongs to
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
        sales_price (Union[None, Unset, float]): Default sales price (excluding tax), which is automatically assigned to
            the service when creating sales orders
        default_cost (Union[None, Unset, float]): Default cost which is used to calculate profit
        type_ (Union[Unset, ServiceVariantType]): Type classification - always 'service' for service variants
        custom_fields (Union[Unset, list['ServiceVariantCustomFieldsItem']]): Custom field values specific to this
            service variant
    """

    id: int
    sku: str
    service_id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    sales_price: None | Unset | float = UNSET
    default_cost: None | Unset | float = UNSET
    type_: Unset | ServiceVariantType = UNSET
    custom_fields: Unset | list["ServiceVariantCustomFieldsItem"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sku = self.sku

        service_id = self.service_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        sales_price: None | Unset | float
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        else:
            sales_price = self.sales_price

        default_cost: None | Unset | float
        if isinstance(self.default_cost, Unset):
            default_cost = UNSET
        else:
            default_cost = self.default_cost

        type_: Unset | str = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

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
                "sku": sku,
                "service_id": service_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if default_cost is not UNSET:
            field_dict["default_cost"] = default_cost
        if type_ is not UNSET:
            field_dict["type"] = type_
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_variant_custom_fields_item import (
            ServiceVariantCustomFieldsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        sku = d.pop("sku")

        service_id = d.pop("service_id")

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        def _parse_sales_price(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_default_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        default_cost = _parse_default_cost(d.pop("default_cost", UNSET))

        _type_ = d.pop("type", UNSET)
        type_: Unset | ServiceVariantType
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ServiceVariantType(_type_)

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = ServiceVariantCustomFieldsItem.from_dict(
                custom_fields_item_data
            )

            custom_fields.append(custom_fields_item)

        service_variant = cls(
            id=id,
            sku=sku,
            service_id=service_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            sales_price=sales_price,
            default_cost=default_cost,
            type_=type_,
            custom_fields=custom_fields,
        )

        service_variant.additional_properties = d
        return service_variant

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
