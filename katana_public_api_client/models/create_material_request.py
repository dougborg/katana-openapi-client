from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_variant_request import CreateVariantRequest
    from ..models.material_config import MaterialConfig


T = TypeVar("T", bound="CreateMaterialRequest")


@_attrs_define
class CreateMaterialRequest:
    """Request payload for creating a new raw material with variants and specifications

    Example:
        {'name': 'Stainless Steel Sheet 304', 'uom': 'm²', 'category_name': 'Raw Materials', 'default_supplier_id':
            1501, 'additional_info': 'Food-grade stainless steel, 1.5mm thickness', 'batch_tracked': True, 'is_sellable':
            False, 'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'name': 'Grade', 'values':
            ['304', '316']}, {'name': 'Thickness', 'values': ['1.5mm', '2.0mm', '3.0mm']}], 'variants': [{'sku':
            'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price': 45.0, 'lead_time': 5, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Grade', 'config_value': '304'}, {'config_name': 'Thickness',
            'config_value': '1.5mm'}]}]}

    Attributes:
        name (str): Display name for the material used in inventory and manufacturing
        variants (list['CreateVariantRequest']): Material variants with specific configurations and properties
        uom (Union[Unset, str]): Unit of measure for inventory tracking (e.g., kg, lb, pcs)
        category_name (Union[Unset, str]): Material category for organization and classification
        default_supplier_id (Union[Unset, int]): Primary supplier for purchasing this material
        additional_info (Union[Unset, str]): Additional specifications or notes about the material
        batch_tracked (Union[Unset, bool]): Whether this material uses batch tracking for quality control
        is_sellable (Union[Unset, bool]): Whether this material can be sold directly to customers
        purchase_uom (Union[Unset, str]): If you are purchasing in a different unit of measure than the default unit of
            measure (used for tracking stock)
            for this item, you can define the purchase unit. Value null indicates that purchasing is done in same unit
            of measure. If value is not null, purchase_uom_conversion_rate must also be populated.
        purchase_uom_conversion_rate (Union[Unset, float]): The conversion rate between the purchase and material UoMs.
            If used, material must have a purchase_uom
            that is different from uom.
        configs (Union[Unset, list['MaterialConfig']]): Material configuration options for creating variants
    """

    name: str
    variants: list["CreateVariantRequest"]
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    default_supplier_id: Unset | int = UNSET
    additional_info: Unset | str = UNSET
    batch_tracked: Unset | bool = UNSET
    is_sellable: Unset | bool = UNSET
    purchase_uom: Unset | str = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    configs: Unset | list["MaterialConfig"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        variants = []
        for variants_item_data in self.variants:
            variants_item = variants_item_data.to_dict()
            variants.append(variants_item)

        uom = self.uom

        category_name = self.category_name

        default_supplier_id = self.default_supplier_id

        additional_info = self.additional_info

        batch_tracked = self.batch_tracked

        is_sellable = self.is_sellable

        purchase_uom = self.purchase_uom

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        configs: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.configs, Unset):
            configs = []
            for configs_item_data in self.configs:
                configs_item = configs_item_data.to_dict()
                configs.append(configs_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "variants": variants,
            }
        )
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if default_supplier_id is not UNSET:
            field_dict["default_supplier_id"] = default_supplier_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_tracked is not UNSET:
            field_dict["batch_tracked"] = batch_tracked
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if configs is not UNSET:
            field_dict["configs"] = configs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_variant_request import CreateVariantRequest
        from ..models.material_config import MaterialConfig

        d = dict(src_dict)
        name = d.pop("name")

        variants = []
        _variants = d.pop("variants")
        for variants_item_data in _variants:
            variants_item = CreateVariantRequest.from_dict(variants_item_data)

            variants.append(variants_item)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        default_supplier_id = d.pop("default_supplier_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        batch_tracked = d.pop("batch_tracked", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        configs = []
        _configs = d.pop("configs", UNSET)
        for configs_item_data in _configs or []:
            configs_item = MaterialConfig.from_dict(configs_item_data)

            configs.append(configs_item)

        create_material_request = cls(
            name=name,
            variants=variants,
            uom=uom,
            category_name=category_name,
            default_supplier_id=default_supplier_id,
            additional_info=additional_info,
            batch_tracked=batch_tracked,
            is_sellable=is_sellable,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            configs=configs,
        )

        return create_material_request
