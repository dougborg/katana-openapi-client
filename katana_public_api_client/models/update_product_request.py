from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_product_request_configs_item import (
        UpdateProductRequestConfigsItem,
    )


T = TypeVar("T", bound="UpdateProductRequest")


@_attrs_define
class UpdateProductRequest:
    """Request payload for updating an existing finished product's properties, configurations, and manufacturing
    specifications

        Example:
            {'name': 'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Premium Kitchenware', 'is_sellable':
                True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False, 'default_supplier_id': None,
                'additional_info': 'High-carbon stainless steel with ergonomic handles, dishwasher safe', 'batch_tracked':
                False, 'serial_tracked': True, 'operations_in_sequence': True, 'purchase_uom': 'set',
                'purchase_uom_conversion_rate': 1.0, 'custom_field_collection_id': 5, 'configs': [{'name': 'Piece Count',
                'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values': ['Wood', 'Steel',
                'Composite']}]}

        Attributes:
            name (Union[Unset, str]): Display name for the finished product used in sales and manufacturing
            uom (Union[Unset, str]): Unit of measurement for the product (e.g., pcs, kg, m)
            category_name (Union[Unset, str]): Product category for organizational grouping and reporting
            is_sellable (Union[Unset, bool]): Whether this product can be sold to customers
            is_producible (Union[Unset, bool]): Whether this product can be manufactured in-house
            is_purchasable (Union[Unset, bool]): Whether this product can be purchased from suppliers
            is_auto_assembly (Union[Unset, bool]): Whether the product should be automatically assembled when components are
                available
            default_supplier_id (Union[Unset, int]): Primary supplier ID for purchasing this product
            additional_info (Union[Unset, str]): Additional notes or specifications for the product
            batch_tracked (Union[Unset, bool]): Whether inventory movements are tracked by batch numbers
            serial_tracked (Union[Unset, bool]): Whether inventory movements are tracked by individual serial numbers
            operations_in_sequence (Union[Unset, bool]): Whether manufacturing operations must be completed in a specific
                sequence
            purchase_uom (Union[Unset, str]): If you are purchasing in a different unit of measure than the default unit of
                measure (used for tracking stock)
                for this item, you can define the purchase unit. Value null indicates that purchasing is done in same unit
                of measure. If value is not null, purchase_uom_conversion_rate must also be populated.
            purchase_uom_conversion_rate (Union[Unset, float]): The conversion rate between the purchase and product UoMs.
                If used, product must have a purchase_uom
                that is different from uom.
            configs (Union[Unset, list['UpdateProductRequestConfigsItem']]): Configuration attributes that define variant
                combinations (size, color, etc.).
                When updating configs, all configs and values must be provided. Existing ones are matched,
                new ones are created, and configs not provided in the update are deleted.
                If you want to remove all configs, delete variants first, then you can omit this field.
            custom_field_collection_id (Union[None, Unset, int]): ID of the custom field collection associated with this
                product
    """

    name: Unset | str = UNSET
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
    configs: Unset | list["UpdateProductRequestConfigsItem"] = UNSET
    custom_field_collection_id: None | Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

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

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
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
        if configs is not UNSET:
            field_dict["configs"] = configs
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_product_request_configs_item import (
            UpdateProductRequestConfigsItem,
        )

        d = dict(src_dict)
        name = d.pop("name", UNSET)

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

        configs = []
        _configs = d.pop("configs", UNSET)
        for configs_item_data in _configs or []:
            configs_item = UpdateProductRequestConfigsItem.from_dict(configs_item_data)

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

        update_product_request = cls(
            name=name,
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
            configs=configs,
            custom_field_collection_id=custom_field_collection_id,
        )

        return update_product_request
