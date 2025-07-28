from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_variant_request_config_attributes_item import (
        UpdateVariantRequestConfigAttributesItem,
    )
    from ..models.update_variant_request_custom_fields_item import (
        UpdateVariantRequestCustomFieldsItem,
    )


T = TypeVar("T", bound="UpdateVariantRequest")


@_attrs_define
class UpdateVariantRequest:
    sku: Unset | str = UNSET
    sales_price: Unset | float = UNSET
    purchase_price: Unset | float = UNSET
    product_id: None | Unset | int = UNSET
    material_id: None | Unset | int = UNSET
    supplier_item_codes: Unset | list[str] = UNSET
    internal_barcode: Unset | str = UNSET
    registered_barcode: Unset | str = UNSET
    lead_time: None | Unset | int = UNSET
    minimum_order_quantity: Unset | float = UNSET
    config_attributes: Unset | list["UpdateVariantRequestConfigAttributesItem"] = UNSET
    custom_fields: Unset | list["UpdateVariantRequestCustomFieldsItem"] = UNSET

    def to_dict(self) -> dict[str, Any]:
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

        supplier_item_codes: Unset | list[str] = UNSET
        if not isinstance(self.supplier_item_codes, Unset):
            supplier_item_codes = self.supplier_item_codes

        internal_barcode = self.internal_barcode

        registered_barcode = self.registered_barcode

        lead_time: None | Unset | int
        if isinstance(self.lead_time, Unset):
            lead_time = UNSET
        else:
            lead_time = self.lead_time

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

        field_dict: dict[str, Any] = {}

        field_dict.update({})
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
        if supplier_item_codes is not UNSET:
            field_dict["supplier_item_codes"] = supplier_item_codes
        if internal_barcode is not UNSET:
            field_dict["internal_barcode"] = internal_barcode
        if registered_barcode is not UNSET:
            field_dict["registered_barcode"] = registered_barcode
        if lead_time is not UNSET:
            field_dict["lead_time"] = lead_time
        if minimum_order_quantity is not UNSET:
            field_dict["minimum_order_quantity"] = minimum_order_quantity
        if config_attributes is not UNSET:
            field_dict["config_attributes"] = config_attributes
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_variant_request_config_attributes_item import (
            UpdateVariantRequestConfigAttributesItem,
        )
        from ..models.update_variant_request_custom_fields_item import (
            UpdateVariantRequestCustomFieldsItem,
        )

        d = dict(src_dict)
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

        supplier_item_codes = cast(list[str], d.pop("supplier_item_codes", UNSET))

        internal_barcode = d.pop("internal_barcode", UNSET)

        registered_barcode = d.pop("registered_barcode", UNSET)

        def _parse_lead_time(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        lead_time = _parse_lead_time(d.pop("lead_time", UNSET))

        minimum_order_quantity = d.pop("minimum_order_quantity", UNSET)

        config_attributes = []
        _config_attributes = d.pop("config_attributes", UNSET)
        for config_attributes_item_data in _config_attributes or []:
            config_attributes_item = UpdateVariantRequestConfigAttributesItem.from_dict(
                config_attributes_item_data
            )

            config_attributes.append(config_attributes_item)

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = UpdateVariantRequestCustomFieldsItem.from_dict(
                custom_fields_item_data
            )

            custom_fields.append(custom_fields_item)

        update_variant_request = cls(
            sku=sku,
            sales_price=sales_price,
            purchase_price=purchase_price,
            product_id=product_id,
            material_id=material_id,
            supplier_item_codes=supplier_item_codes,
            internal_barcode=internal_barcode,
            registered_barcode=registered_barcode,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            config_attributes=config_attributes,
            custom_fields=custom_fields,
        )

        return update_variant_request
