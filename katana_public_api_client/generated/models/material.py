import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.material_configs_item import MaterialConfigsItem
    from ..models.material_supplier import MaterialSupplier
    from ..models.material_variants_item import MaterialVariantsItem


T = TypeVar("T", bound="Material")


@_attrs_define
class Material:
    id: Unset | int = UNSET
    name: Unset | str = UNSET
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    default_supplier_id: Unset | int = UNSET
    additional_info: Unset | str = UNSET
    batch_tracked: Unset | bool = UNSET
    is_sellable: Unset | bool = UNSET
    type_: Unset | str = UNSET
    purchase_uom: Unset | str = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    variants: Unset | list["MaterialVariantsItem"] = UNSET
    configs: Unset | list["MaterialConfigsItem"] = UNSET
    custom_field_collection_id: Unset | int = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    archived_at: None | Unset | datetime.datetime = UNSET
    supplier: Union[Unset, "MaterialSupplier"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        uom = self.uom

        category_name = self.category_name

        default_supplier_id = self.default_supplier_id

        additional_info = self.additional_info

        batch_tracked = self.batch_tracked

        is_sellable = self.is_sellable

        type_ = self.type_

        purchase_uom = self.purchase_uom

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        variants: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.variants, Unset):
            variants = []
            for variants_item_data in self.variants:
                variants_item = variants_item_data.to_dict()
                variants.append(variants_item)

        configs: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.configs, Unset):
            configs = []
            for configs_item_data in self.configs:
                configs_item = configs_item_data.to_dict()
                configs.append(configs_item)

        custom_field_collection_id = self.custom_field_collection_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        archived_at: None | Unset | str
        if isinstance(self.archived_at, Unset):
            archived_at = UNSET
        elif isinstance(self.archived_at, datetime.datetime):
            archived_at = self.archived_at.isoformat()
        else:
            archived_at = self.archived_at

        supplier: Unset | dict[str, Any] = UNSET
        if not isinstance(self.supplier, Unset):
            supplier = self.supplier.to_dict()

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
        if default_supplier_id is not UNSET:
            field_dict["default_supplier_id"] = default_supplier_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_tracked is not UNSET:
            field_dict["batch_tracked"] = batch_tracked
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if type_ is not UNSET:
            field_dict["type"] = type_
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if variants is not UNSET:
            field_dict["variants"] = variants
        if configs is not UNSET:
            field_dict["configs"] = configs
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if archived_at is not UNSET:
            field_dict["archived_at"] = archived_at
        if supplier is not UNSET:
            field_dict["supplier"] = supplier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.material_configs_item import MaterialConfigsItem
        from ..models.material_supplier import MaterialSupplier
        from ..models.material_variants_item import MaterialVariantsItem

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        default_supplier_id = d.pop("default_supplier_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        batch_tracked = d.pop("batch_tracked", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        type_ = d.pop("type", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        variants = []
        _variants = d.pop("variants", UNSET)
        for variants_item_data in _variants or []:
            variants_item = MaterialVariantsItem.from_dict(variants_item_data)

            variants.append(variants_item)

        configs = []
        _configs = d.pop("configs", UNSET)
        for configs_item_data in _configs or []:
            configs_item = MaterialConfigsItem.from_dict(configs_item_data)

            configs.append(configs_item)

        custom_field_collection_id = d.pop("custom_field_collection_id", UNSET)

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

        def _parse_archived_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                archived_at_type_0 = isoparse(data)

                return archived_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        archived_at = _parse_archived_at(d.pop("archived_at", UNSET))

        _supplier = d.pop("supplier", UNSET)
        supplier: Unset | MaterialSupplier
        if isinstance(_supplier, Unset):
            supplier = UNSET
        else:
            supplier = MaterialSupplier.from_dict(_supplier)

        material = cls(
            id=id,
            name=name,
            uom=uom,
            category_name=category_name,
            default_supplier_id=default_supplier_id,
            additional_info=additional_info,
            batch_tracked=batch_tracked,
            is_sellable=is_sellable,
            type_=type_,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            variants=variants,
            configs=configs,
            custom_field_collection_id=custom_field_collection_id,
            created_at=created_at,
            updated_at=updated_at,
            archived_at=archived_at,
            supplier=supplier,
        )

        material.additional_properties = d
        return material

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
