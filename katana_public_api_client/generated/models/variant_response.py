import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.variant_response_type import VariantResponseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant_response_config_attributes_item import (
        VariantResponseConfigAttributesItem,
    )
    from ..models.variant_response_custom_fields_item import (
        VariantResponseCustomFieldsItem,
    )
    from ..models.variant_response_product_or_material import (
        VariantResponseProductOrMaterial,
    )


T = TypeVar("T", bound="VariantResponse")


@_attrs_define
class VariantResponse:
    id: Unset | int = UNSET
    sku: Unset | str = UNSET
    sales_price: Unset | float = UNSET
    purchase_price: Unset | float = UNSET
    product_id: None | Unset | int = UNSET
    material_id: None | Unset | int = UNSET
    type_: Unset | VariantResponseType = UNSET
    internal_barcode: Unset | str = UNSET
    registered_barcode: Unset | str = UNSET
    supplier_item_codes: Unset | list[str] = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    lead_time: None | Unset | int = UNSET
    minimum_order_quantity: None | Unset | float = UNSET
    config_attributes: Unset | list["VariantResponseConfigAttributesItem"] = UNSET
    custom_fields: Unset | list["VariantResponseCustomFieldsItem"] = UNSET
    product_or_material: Union[Unset, "VariantResponseProductOrMaterial"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sku = self.sku

        sales_price = self.sales_price

        purchase_price = self.purchase_price

        product_id: None | Unset | int
        if isinstance(self.product_id, Unset):
            product_id = UNSET
        else:
            product_id = self.product_id

        material_id: None | Unset | int
        if isinstance(self.material_id, Unset):
            material_id = UNSET
        else:
            material_id = self.material_id

        type_: Unset | str = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        internal_barcode = self.internal_barcode

        registered_barcode = self.registered_barcode

        supplier_item_codes: Unset | list[str] = UNSET
        if not isinstance(self.supplier_item_codes, Unset):
            supplier_item_codes = self.supplier_item_codes

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

        lead_time: None | Unset | int
        if isinstance(self.lead_time, Unset):
            lead_time = UNSET
        else:
            lead_time = self.lead_time

        minimum_order_quantity: None | Unset | float
        if isinstance(self.minimum_order_quantity, Unset):
            minimum_order_quantity = UNSET
        else:
            minimum_order_quantity = self.minimum_order_quantity

        config_attributes: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.config_attributes, Unset):
            config_attributes = []
            for config_attributes_item_data in self.config_attributes:
                config_attributes_item = config_attributes_item_data.to_dict()
                config_attributes.append(config_attributes_item)

        custom_fields: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.custom_fields, Unset):
            custom_fields = []
            for custom_fields_item_data in self.custom_fields:
                custom_fields_item = custom_fields_item_data.to_dict()
                custom_fields.append(custom_fields_item)

        product_or_material: Unset | dict[str, Any] = UNSET
        if not isinstance(self.product_or_material, Unset):
            product_or_material = self.product_or_material.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if sku is not UNSET:
            field_dict["sku"] = sku
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if purchase_price is not UNSET:
            field_dict["purchase_price"] = purchase_price
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if material_id is not UNSET:
            field_dict["material_id"] = material_id
        if type_ is not UNSET:
            field_dict["type"] = type_
        if internal_barcode is not UNSET:
            field_dict["internal_barcode"] = internal_barcode
        if registered_barcode is not UNSET:
            field_dict["registered_barcode"] = registered_barcode
        if supplier_item_codes is not UNSET:
            field_dict["supplier_item_codes"] = supplier_item_codes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if lead_time is not UNSET:
            field_dict["lead_time"] = lead_time
        if minimum_order_quantity is not UNSET:
            field_dict["minimum_order_quantity"] = minimum_order_quantity
        if config_attributes is not UNSET:
            field_dict["config_attributes"] = config_attributes
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
        if product_or_material is not UNSET:
            field_dict["product_or_material"] = product_or_material

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.variant_response_config_attributes_item import (
            VariantResponseConfigAttributesItem,
        )
        from ..models.variant_response_custom_fields_item import (
            VariantResponseCustomFieldsItem,
        )
        from ..models.variant_response_product_or_material import (
            VariantResponseProductOrMaterial,
        )

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        sku = d.pop("sku", UNSET)

        sales_price = d.pop("sales_price", UNSET)

        purchase_price = d.pop("purchase_price", UNSET)

        def _parse_product_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        product_id = _parse_product_id(d.pop("product_id", UNSET))

        def _parse_material_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        material_id = _parse_material_id(d.pop("material_id", UNSET))

        _type_ = d.pop("type", UNSET)
        type_: Unset | VariantResponseType
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = VariantResponseType(_type_)

        internal_barcode = d.pop("internal_barcode", UNSET)

        registered_barcode = d.pop("registered_barcode", UNSET)

        supplier_item_codes = cast(list[str], d.pop("supplier_item_codes", UNSET))

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

        def _parse_lead_time(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        lead_time = _parse_lead_time(d.pop("lead_time", UNSET))

        def _parse_minimum_order_quantity(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        minimum_order_quantity = _parse_minimum_order_quantity(
            d.pop("minimum_order_quantity", UNSET)
        )

        config_attributes = []
        _config_attributes = d.pop("config_attributes", UNSET)
        for config_attributes_item_data in _config_attributes or []:
            config_attributes_item = VariantResponseConfigAttributesItem.from_dict(
                config_attributes_item_data
            )

            config_attributes.append(config_attributes_item)

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = VariantResponseCustomFieldsItem.from_dict(
                custom_fields_item_data
            )

            custom_fields.append(custom_fields_item)

        _product_or_material = d.pop("product_or_material", UNSET)
        product_or_material: Unset | VariantResponseProductOrMaterial
        if isinstance(_product_or_material, Unset):
            product_or_material = UNSET
        else:
            product_or_material = VariantResponseProductOrMaterial.from_dict(
                _product_or_material
            )

        variant_response = cls(
            id=id,
            sku=sku,
            sales_price=sales_price,
            purchase_price=purchase_price,
            product_id=product_id,
            material_id=material_id,
            type_=type_,
            internal_barcode=internal_barcode,
            registered_barcode=registered_barcode,
            supplier_item_codes=supplier_item_codes,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            config_attributes=config_attributes,
            custom_fields=custom_fields,
            product_or_material=product_or_material,
        )

        variant_response.additional_properties = d
        return variant_response

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
