from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_product_request_configs_item import (
        CreateProductRequestConfigsItem,
    )
    from ..models.create_variant_request import CreateVariantRequest


T = TypeVar("T", bound="CreateProductRequest")


@_attrs_define
class CreateProductRequest:
    """Request payload for creating a new finished product with variants, configurations, and manufacturing specifications

    Example:
        {'name': 'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchen Equipment', 'is_sellable':
            True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False, 'additional_info': 'High-
            quality steel construction with ergonomic handles', 'batch_tracked': False, 'serial_tracked': True,
            'operations_in_sequence': True, 'lead_time': 14, 'minimum_order_quantity': 1, 'configs': [{'name': 'Piece
            Count', 'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values': ['Steel', 'Wooden',
            'Composite']}], 'variants': [{'sku': 'KNF-PRO-8PC-STL', 'sales_price': 299.99, 'purchase_price': 150.0,
            'supplier_item_codes': ['KNF-8PC-STEEL-001'], 'lead_time': 14, 'minimum_order_quantity': 1, 'config_attributes':
            [{'config_name': 'Piece Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}]}

    Attributes:
        name (str): Display name for the finished product used in sales and manufacturing
        variants (list['CreateVariantRequest']): Product variants with specific configurations and properties
        uom (Union[Unset, str]): Base unit of measure for the product (e.g., pcs, kg, m)
        category_name (Union[Unset, str]): Product category for organization and reporting purposes
        is_sellable (Union[Unset, bool]): Whether this product can be included in sales orders
        is_producible (Union[Unset, bool]): Whether this product can be manufactured using recipes
        is_purchasable (Union[Unset, bool]): Whether this product can be purchased from suppliers
        is_auto_assembly (Union[Unset, bool]): Whether assembly operations are automatically performed when stock is
            available
        default_supplier_id (Union[Unset, int]): Primary supplier for purchasing this product
        additional_info (Union[Unset, str]): Additional notes or specifications for the product
        batch_tracked (Union[Unset, bool]): Whether this product uses batch tracking for inventory management
        serial_tracked (Union[Unset, bool]): Whether this product uses serial number tracking for individual units
        operations_in_sequence (Union[Unset, bool]): Whether manufacturing operations must be completed in sequence
        purchase_uom (Union[Unset, str]): If you are purchasing in a different unit of measure than the default unit of
            measure (used for tracking stock)
            for this item, you can define the purchase unit. Value null indicates that purchasing is done in same unit
            of measure. If value is not null, purchase_uom_conversion_rate must also be populated.
        purchase_uom_conversion_rate (Union[Unset, float]): The conversion rate between the purchase and product UoMs.
            If used, product must have a purchase_uom
            that is different from uom.
        lead_time (Union[None, Unset, int]): Expected lead time in days for procurement or production
        minimum_order_quantity (Union[Unset, float]): Minimum quantity that must be ordered from suppliers
        configs (Union[Unset, list['CreateProductRequestConfigsItem']]): Product configuration options for creating
            variants
        custom_field_collection_id (Union[None, Unset, int]): Reference to custom field collection for additional
            product data
    """

    name: str
    variants: list["CreateVariantRequest"]
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    is_sellable: Unset | bool = UNSET
    is_producible: Unset | bool = UNSET
    is_purchasable: Unset | bool = UNSET
    is_auto_assembly: Unset | bool = UNSET
    default_supplier_id: Unset | int = UNSET
    additional_info: Unset | str = UNSET
    batch_tracked: Unset | bool = UNSET
    serial_tracked: Unset | bool = UNSET
    operations_in_sequence: Unset | bool = UNSET
    purchase_uom: Unset | str = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    lead_time: None | Unset | int = UNSET
    minimum_order_quantity: Unset | float = UNSET
    configs: Unset | list["CreateProductRequestConfigsItem"] = UNSET
    custom_field_collection_id: None | Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        variants = []
        for variants_item_data in self.variants:
            variants_item = variants_item_data.to_dict()
            variants.append(variants_item)

        uom = self.uom

        category_name = self.category_name

        is_sellable = self.is_sellable

        is_producible = self.is_producible

        is_purchasable = self.is_purchasable

        is_auto_assembly = self.is_auto_assembly

        default_supplier_id = self.default_supplier_id

        additional_info = self.additional_info

        batch_tracked = self.batch_tracked

        serial_tracked = self.serial_tracked

        operations_in_sequence = self.operations_in_sequence

        purchase_uom = self.purchase_uom

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        lead_time: None | Unset | int
        if isinstance(self.lead_time, Unset):
            lead_time = UNSET
        else:
            lead_time = self.lead_time

        minimum_order_quantity = self.minimum_order_quantity

        configs: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.configs, Unset):
            configs = []
            for configs_item_data in self.configs:
                configs_item = configs_item_data.to_dict()
                configs.append(configs_item)

        custom_field_collection_id: None | Unset | int
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

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
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if is_producible is not UNSET:
            field_dict["is_producible"] = is_producible
        if is_purchasable is not UNSET:
            field_dict["is_purchasable"] = is_purchasable
        if is_auto_assembly is not UNSET:
            field_dict["is_auto_assembly"] = is_auto_assembly
        if default_supplier_id is not UNSET:
            field_dict["default_supplier_id"] = default_supplier_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_tracked is not UNSET:
            field_dict["batch_tracked"] = batch_tracked
        if serial_tracked is not UNSET:
            field_dict["serial_tracked"] = serial_tracked
        if operations_in_sequence is not UNSET:
            field_dict["operations_in_sequence"] = operations_in_sequence
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if lead_time is not UNSET:
            field_dict["lead_time"] = lead_time
        if minimum_order_quantity is not UNSET:
            field_dict["minimum_order_quantity"] = minimum_order_quantity
        if configs is not UNSET:
            field_dict["configs"] = configs
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_product_request_configs_item import (
            CreateProductRequestConfigsItem,
        )
        from ..models.create_variant_request import CreateVariantRequest

        d = dict(src_dict)
        name = d.pop("name")

        variants = []
        _variants = d.pop("variants")
        for variants_item_data in _variants:
            variants_item = CreateVariantRequest.from_dict(variants_item_data)

            variants.append(variants_item)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        is_producible = d.pop("is_producible", UNSET)

        is_purchasable = d.pop("is_purchasable", UNSET)

        is_auto_assembly = d.pop("is_auto_assembly", UNSET)

        default_supplier_id = d.pop("default_supplier_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        batch_tracked = d.pop("batch_tracked", UNSET)

        serial_tracked = d.pop("serial_tracked", UNSET)

        operations_in_sequence = d.pop("operations_in_sequence", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        def _parse_lead_time(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        lead_time = _parse_lead_time(d.pop("lead_time", UNSET))

        minimum_order_quantity = d.pop("minimum_order_quantity", UNSET)

        configs = []
        _configs = d.pop("configs", UNSET)
        for configs_item_data in _configs or []:
            configs_item = CreateProductRequestConfigsItem.from_dict(configs_item_data)

            configs.append(configs_item)

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        create_product_request = cls(
            name=name,
            variants=variants,
            uom=uom,
            category_name=category_name,
            is_sellable=is_sellable,
            is_producible=is_producible,
            is_purchasable=is_purchasable,
            is_auto_assembly=is_auto_assembly,
            default_supplier_id=default_supplier_id,
            additional_info=additional_info,
            batch_tracked=batch_tracked,
            serial_tracked=serial_tracked,
            operations_in_sequence=operations_in_sequence,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            lead_time=lead_time,
            minimum_order_quantity=minimum_order_quantity,
            configs=configs,
            custom_field_collection_id=custom_field_collection_id,
        )

        return create_product_request
