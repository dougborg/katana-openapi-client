from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_material_variant_request_config_attributes_item import (
        CreateMaterialVariantRequestConfigAttributesItem,
    )
    from ..models.create_material_variant_request_custom_fields_item import (
        CreateMaterialVariantRequestCustomFieldsItem,
    )
    from ..models.create_material_variant_request_custom_fields_type_0 import (
        CreateMaterialVariantRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="CreateMaterialVariantRequest")


@_attrs_define
class CreateMaterialVariantRequest:
    """Variant embedded in POST /materials. The material parent is implicit.
    Unlike product creation and POST /variants, this shape rejects sales_price.
    Set a material selling price afterward with PATCH /variants/{id}.

        Example:
            {'sku': 'KNF-PRO-12PC-WD', 'purchase_price': 200.0, 'supplier_item_codes': ['SUP-KNF-12PC-002'],
                'internal_barcode': 'INT-KNF-002', 'registered_barcode': '789123456790', 'lead_time': 10,
                'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'},
                {'config_name': 'Handle Material', 'config_value': 'Wood'}], 'custom_fields': [{'field_name': 'Warranty Period',
                'field_value': '5 years'}, {'field_name': 'Care Instructions', 'field_value': 'Hand wash only'}]}
    """

    sku: str | Unset = UNSET
    purchase_price: float | Unset | None = UNSET
    supplier_item_codes: list[str] | Unset = UNSET
    internal_barcode: str | Unset = UNSET
    registered_barcode: str | Unset = UNSET
    lead_time: int | Unset | None = UNSET
    minimum_order_quantity: float | Unset | None = UNSET
    config_attributes: (
        list[CreateMaterialVariantRequestConfigAttributesItem] | Unset
    ) = UNSET
    custom_fields: (
        CreateMaterialVariantRequestCustomFieldsType0
        | list[CreateMaterialVariantRequestCustomFieldsItem]
        | Unset
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_material_variant_request_custom_fields_type_0 import (
            CreateMaterialVariantRequestCustomFieldsType0,
        )

        sku = self.sku

        purchase_price: float | Unset | None
        if isinstance(self.purchase_price, Unset):
            purchase_price = UNSET
        else:
            purchase_price = self.purchase_price

        supplier_item_codes: list[str] | Unset = UNSET
        if not isinstance(self.supplier_item_codes, Unset):
            supplier_item_codes = self.supplier_item_codes

        internal_barcode = self.internal_barcode

        registered_barcode = self.registered_barcode

        lead_time: int | Unset | None
        if isinstance(self.lead_time, Unset):
            lead_time = UNSET
        else:
            lead_time = self.lead_time

        minimum_order_quantity: float | Unset | None
        if isinstance(self.minimum_order_quantity, Unset):
            minimum_order_quantity = UNSET
        else:
            minimum_order_quantity = self.minimum_order_quantity

        config_attributes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.config_attributes, Unset):
            config_attributes = []
            for config_attributes_item_data in self.config_attributes:
                config_attributes_item = config_attributes_item_data.to_dict()
                config_attributes.append(config_attributes_item)

        custom_fields: dict[str, Any] | list[dict[str, Any]] | Unset
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, CreateMaterialVariantRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = []
            for custom_fields_type_1_item_data in self.custom_fields:
                custom_fields_type_1_item = custom_fields_type_1_item_data.to_dict()
                custom_fields.append(custom_fields_type_1_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if sku is not UNSET:
            field_dict["sku"] = sku
        if purchase_price is not UNSET:
            field_dict["purchase_price"] = purchase_price
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
        from ..models.create_material_variant_request_config_attributes_item import (
            CreateMaterialVariantRequestConfigAttributesItem,
        )
        from ..models.create_material_variant_request_custom_fields_item import (
            CreateMaterialVariantRequestCustomFieldsItem,
        )
        from ..models.create_material_variant_request_custom_fields_type_0 import (
            CreateMaterialVariantRequestCustomFieldsType0,
        )

        d = dict(src_dict)
        sku = d.pop("sku", UNSET)

        def _parse_purchase_price(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        purchase_price = _parse_purchase_price(d.pop("purchase_price", UNSET))

        supplier_item_codes = cast(list[str], d.pop("supplier_item_codes", UNSET))

        internal_barcode = d.pop("internal_barcode", UNSET)

        registered_barcode = d.pop("registered_barcode", UNSET)

        def _parse_lead_time(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        lead_time = _parse_lead_time(d.pop("lead_time", UNSET))

        def _parse_minimum_order_quantity(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        minimum_order_quantity = _parse_minimum_order_quantity(
            d.pop("minimum_order_quantity", UNSET)
        )

        _config_attributes = d.pop("config_attributes", UNSET)
        config_attributes: (
            list[CreateMaterialVariantRequestConfigAttributesItem] | Unset
        ) = UNSET
        if _config_attributes is not UNSET:
            config_attributes = []
            for config_attributes_item_data in _config_attributes:
                config_attributes_item = (
                    CreateMaterialVariantRequestConfigAttributesItem.from_dict(
                        cast(Mapping[str, Any], config_attributes_item_data)
                    )
                )

                config_attributes.append(config_attributes_item)

        def _parse_custom_fields(
            data: object,
        ) -> (
            CreateMaterialVariantRequestCustomFieldsType0
            | list[CreateMaterialVariantRequestCustomFieldsItem]
            | Unset
        ):
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    CreateMaterialVariantRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, list):
                raise TypeError()
            custom_fields_type_1 = []
            _custom_fields_type_1 = data
            for custom_fields_type_1_item_data in _custom_fields_type_1:
                custom_fields_type_1_item = (
                    CreateMaterialVariantRequestCustomFieldsItem.from_dict(
                        cast(Mapping[str, Any], custom_fields_type_1_item_data)
                    )
                )

                custom_fields_type_1.append(custom_fields_type_1_item)

            return custom_fields_type_1

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        create_material_variant_request = cls(
            sku=sku,
            purchase_price=purchase_price,
            supplier_item_codes=supplier_item_codes,
            internal_barcode=internal_barcode,
            registered_barcode=registered_barcode,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            config_attributes=config_attributes,
            custom_fields=custom_fields,
        )

        return create_material_variant_request
