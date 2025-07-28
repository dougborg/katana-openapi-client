from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_material_request_variants_item_config_attributes_item import (
        CreateMaterialRequestVariantsItemConfigAttributesItem,
    )
    from ..models.create_material_request_variants_item_custom_fields_item import (
        CreateMaterialRequestVariantsItemCustomFieldsItem,
    )


T = TypeVar("T", bound="CreateMaterialRequestVariantsItem")


@_attrs_define
class CreateMaterialRequestVariantsItem:
    sku: Unset | str = UNSET
    purchase_price: Unset | float = UNSET
    internal_barcode: Unset | str = UNSET
    registered_barcode: Unset | str = UNSET
    supplier_item_codes: Unset | list[str] = UNSET
    lead_time: Unset | float = UNSET
    minimum_order_quantity: Unset | float = UNSET
    config_attributes: (
        Unset | list["CreateMaterialRequestVariantsItemConfigAttributesItem"]
    ) = UNSET
    custom_field_collection_id: None | Unset | int = UNSET
    custom_fields: Unset | list["CreateMaterialRequestVariantsItemCustomFieldsItem"] = (
        UNSET
    )

    def to_dict(self) -> dict[str, Any]:
        sku = self.sku

        purchase_price = self.purchase_price

        internal_barcode = self.internal_barcode

        registered_barcode = self.registered_barcode

        supplier_item_codes: Unset | list[str] = UNSET
        if not isinstance(self.supplier_item_codes, Unset):
            supplier_item_codes = self.supplier_item_codes

        lead_time = self.lead_time

        minimum_order_quantity = self.minimum_order_quantity

        config_attributes: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.config_attributes, Unset):
            config_attributes = []
            for config_attributes_item_data in self.config_attributes:
                config_attributes_item = config_attributes_item_data.to_dict()
                config_attributes.append(config_attributes_item)

        custom_field_collection_id: None | Unset | int
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

        custom_fields: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.custom_fields, Unset):
            custom_fields = []
            for custom_fields_item_data in self.custom_fields:
                custom_fields_item = custom_fields_item_data.to_dict()
                custom_fields.append(custom_fields_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if sku is not UNSET:
            field_dict["sku"] = sku
        if purchase_price is not UNSET:
            field_dict["purchase_price"] = purchase_price
        if internal_barcode is not UNSET:
            field_dict["internal_barcode"] = internal_barcode
        if registered_barcode is not UNSET:
            field_dict["registered_barcode"] = registered_barcode
        if supplier_item_codes is not UNSET:
            field_dict["supplier_item_codes"] = supplier_item_codes
        if lead_time is not UNSET:
            field_dict["lead_time"] = lead_time
        if minimum_order_quantity is not UNSET:
            field_dict["minimum_order_quantity"] = minimum_order_quantity
        if config_attributes is not UNSET:
            field_dict["config_attributes"] = config_attributes
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_material_request_variants_item_config_attributes_item import (
            CreateMaterialRequestVariantsItemConfigAttributesItem,
        )
        from ..models.create_material_request_variants_item_custom_fields_item import (
            CreateMaterialRequestVariantsItemCustomFieldsItem,
        )

        d = dict(src_dict)
        sku = d.pop("sku", UNSET)

        purchase_price = d.pop("purchase_price", UNSET)

        internal_barcode = d.pop("internal_barcode", UNSET)

        registered_barcode = d.pop("registered_barcode", UNSET)

        supplier_item_codes = cast(list[str], d.pop("supplier_item_codes", UNSET))

        lead_time = d.pop("lead_time", UNSET)

        minimum_order_quantity = d.pop("minimum_order_quantity", UNSET)

        config_attributes = []
        _config_attributes = d.pop("config_attributes", UNSET)
        for config_attributes_item_data in _config_attributes or []:
            config_attributes_item = (
                CreateMaterialRequestVariantsItemConfigAttributesItem.from_dict(
                    config_attributes_item_data
                )
            )

            config_attributes.append(config_attributes_item)

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = (
                CreateMaterialRequestVariantsItemCustomFieldsItem.from_dict(
                    custom_fields_item_data
                )
            )

            custom_fields.append(custom_fields_item)

        create_material_request_variants_item = cls(
            sku=sku,
            purchase_price=purchase_price,
            internal_barcode=internal_barcode,
            registered_barcode=registered_barcode,
            supplier_item_codes=supplier_item_codes,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            config_attributes=config_attributes,
            custom_field_collection_id=custom_field_collection_id,
            custom_fields=custom_fields,
        )

        return create_material_request_variants_item
