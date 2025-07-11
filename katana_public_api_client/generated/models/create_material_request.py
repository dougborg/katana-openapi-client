from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_material_request_configs_item import (
        CreateMaterialRequestConfigsItem,
    )
    from ..models.create_material_request_variants_item import (
        CreateMaterialRequestVariantsItem,
    )


T = TypeVar("T", bound="CreateMaterialRequest")


@_attrs_define
class CreateMaterialRequest:
    """
    Attributes:
        name (str):
        variants (list['CreateMaterialRequestVariantsItem']):
        uom (Union[Unset, str]):
        category_name (Union[Unset, str]):
        default_supplier_id (Union[Unset, int]):
        additional_info (Union[Unset, str]):
        batch_tracked (Union[Unset, bool]):
        is_sellable (Union[Unset, bool]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        configs (Union[Unset, list['CreateMaterialRequestConfigsItem']]):
    """

    name: str
    variants: list["CreateMaterialRequestVariantsItem"]
    uom: Union[Unset, str] = UNSET
    category_name: Union[Unset, str] = UNSET
    default_supplier_id: Union[Unset, int] = UNSET
    additional_info: Union[Unset, str] = UNSET
    batch_tracked: Union[Unset, bool] = UNSET
    is_sellable: Union[Unset, bool] = UNSET
    purchase_uom: Union[Unset, str] = UNSET
    purchase_uom_conversion_rate: Union[Unset, float] = UNSET
    configs: Union[Unset, list["CreateMaterialRequestConfigsItem"]] = UNSET

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

        configs: Union[Unset, list[dict[str, Any]]] = UNSET
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
        from ..models.create_material_request_configs_item import (
            CreateMaterialRequestConfigsItem,
        )
        from ..models.create_material_request_variants_item import (
            CreateMaterialRequestVariantsItem,
        )

        d = dict(src_dict)
        name = d.pop("name")

        variants = []
        _variants = d.pop("variants")
        for variants_item_data in _variants:
            variants_item = CreateMaterialRequestVariantsItem.from_dict(
                variants_item_data
            )

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
            configs_item = CreateMaterialRequestConfigsItem.from_dict(configs_item_data)

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
