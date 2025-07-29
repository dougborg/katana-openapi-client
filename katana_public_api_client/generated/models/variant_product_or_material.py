from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant_product_or_material_variants_item import (
        VariantProductOrMaterialVariantsItem,
    )


T = TypeVar("T", bound="VariantProductOrMaterial")


@_attrs_define
class VariantProductOrMaterial:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[Unset, str]):
        uom (Union[Unset, str]):
        category_name (Union[Unset, str]):
        is_producible (Union[Unset, bool]):
        default_supplier_id (Union[Unset, int]):
        is_purchasable (Union[Unset, bool]):
        type_ (Union[Unset, str]):
        purchase_uom (Union[Unset, str]):
        purchase_uom_conversion_rate (Union[Unset, float]):
        batch_tracked (Union[Unset, bool]):
        variants (Union[Unset, list['VariantProductOrMaterialVariantsItem']]):
    """

    id: Unset | int = UNSET
    name: Unset | str = UNSET
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    is_producible: Unset | bool = UNSET
    default_supplier_id: Unset | int = UNSET
    is_purchasable: Unset | bool = UNSET
    type_: Unset | str = UNSET
    purchase_uom: Unset | str = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    batch_tracked: Unset | bool = UNSET
    variants: Unset | list["VariantProductOrMaterialVariantsItem"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        uom = self.uom

        category_name = self.category_name

        is_producible = self.is_producible

        default_supplier_id = self.default_supplier_id

        is_purchasable = self.is_purchasable

        type_ = self.type_

        purchase_uom = self.purchase_uom

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        batch_tracked = self.batch_tracked

        variants: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.variants, Unset):
            variants = []
            for variants_item_data in self.variants:
                variants_item = variants_item_data.to_dict()
                variants.append(variants_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if is_producible is not UNSET:
            field_dict["is_producible"] = is_producible
        if default_supplier_id is not UNSET:
            field_dict["default_supplier_id"] = default_supplier_id
        if is_purchasable is not UNSET:
            field_dict["is_purchasable"] = is_purchasable
        if type_ is not UNSET:
            field_dict["type"] = type_
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if batch_tracked is not UNSET:
            field_dict["batch_tracked"] = batch_tracked
        if variants is not UNSET:
            field_dict["variants"] = variants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.variant_product_or_material_variants_item import (
            VariantProductOrMaterialVariantsItem,
        )

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        is_producible = d.pop("is_producible", UNSET)

        default_supplier_id = d.pop("default_supplier_id", UNSET)

        is_purchasable = d.pop("is_purchasable", UNSET)

        type_ = d.pop("type", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        batch_tracked = d.pop("batch_tracked", UNSET)

        variants = []
        _variants = d.pop("variants", UNSET)
        for variants_item_data in _variants or []:
            variants_item = VariantProductOrMaterialVariantsItem.from_dict(
                variants_item_data
            )

            variants.append(variants_item)

        variant_product_or_material = cls(
            id=id,
            name=name,
            uom=uom,
            category_name=category_name,
            is_producible=is_producible,
            default_supplier_id=default_supplier_id,
            is_purchasable=is_purchasable,
            type_=type_,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            batch_tracked=batch_tracked,
            variants=variants,
        )

        variant_product_or_material.additional_properties = d
        return variant_product_or_material

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
