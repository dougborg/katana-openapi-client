from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_field_value import CustomFieldValue
    from ..models.update_service_request_custom_fields_type_0 import (
        UpdateServiceRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdateServiceRequest")


@_attrs_define
class UpdateServiceRequest:
    """Request payload for updating an existing service's properties and specifications

    Example:
        {'name': 'Updated Assembly Service', 'uom': 'hours', 'category_name': 'Professional Services', 'is_sellable':
            True, 'is_archived': False, 'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}
    """

    name: str | Unset = UNSET
    uom: str | Unset = UNSET
    category_name: str | Unset = UNSET
    additional_info: str | Unset = UNSET
    is_sellable: bool | Unset = UNSET
    is_archived: bool | Unset = UNSET
    sales_price: float | Unset | None = UNSET
    default_cost: float | Unset | None = UNSET
    sku: str | Unset = UNSET
    custom_field_collection_id: int | Unset | None = UNSET
    custom_fields: (
        list[CustomFieldValue] | Unset | UpdateServiceRequestCustomFieldsType0
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_service_request_custom_fields_type_0 import (
            UpdateServiceRequestCustomFieldsType0,
        )

        name = self.name

        uom = self.uom

        category_name = self.category_name

        additional_info = self.additional_info

        is_sellable = self.is_sellable

        is_archived = self.is_archived

        sales_price: float | Unset | None
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        else:
            sales_price = self.sales_price

        default_cost: float | Unset | None
        if isinstance(self.default_cost, Unset):
            default_cost = UNSET
        else:
            default_cost = self.default_cost

        sku = self.sku

        custom_field_collection_id: int | Unset | None
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

        custom_fields: dict[str, Any] | list[dict[str, Any]] | Unset
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(self.custom_fields, UpdateServiceRequestCustomFieldsType0):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = []
            for custom_fields_type_1_item_data in self.custom_fields:
                custom_fields_type_1_item = custom_fields_type_1_item_data.to_dict()
                custom_fields.append(custom_fields_type_1_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if is_archived is not UNSET:
            field_dict["is_archived"] = is_archived
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if default_cost is not UNSET:
            field_dict["default_cost"] = default_cost
        if sku is not UNSET:
            field_dict["sku"] = sku
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_value import CustomFieldValue
        from ..models.update_service_request_custom_fields_type_0 import (
            UpdateServiceRequestCustomFieldsType0,
        )

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        is_archived = d.pop("is_archived", UNSET)

        def _parse_sales_price(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_default_cost(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        default_cost = _parse_default_cost(d.pop("default_cost", UNSET))

        sku = d.pop("sku", UNSET)

        def _parse_custom_field_collection_id(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        def _parse_custom_fields(
            data: object,
        ) -> list[CustomFieldValue] | Unset | UpdateServiceRequestCustomFieldsType0:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = UpdateServiceRequestCustomFieldsType0.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, list):
                raise TypeError()
            custom_fields_type_1 = []
            _custom_fields_type_1 = data
            for custom_fields_type_1_item_data in _custom_fields_type_1:
                custom_fields_type_1_item = CustomFieldValue.from_dict(
                    cast(Mapping[str, Any], custom_fields_type_1_item_data)
                )

                custom_fields_type_1.append(custom_fields_type_1_item)

            return custom_fields_type_1

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        update_service_request = cls(
            name=name,
            uom=uom,
            category_name=category_name,
            additional_info=additional_info,
            is_sellable=is_sellable,
            is_archived=is_archived,
            sales_price=sales_price,
            default_cost=default_cost,
            sku=sku,
            custom_field_collection_id=custom_field_collection_id,
            custom_fields=custom_fields,
        )

        return update_service_request
