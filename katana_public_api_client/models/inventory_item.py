import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.inventory_item_type import InventoryItemType

if TYPE_CHECKING:
    from ..models.item_config import ItemConfig
    from ..models.supplier import Supplier
    from ..models.variant import Variant


T = TypeVar("T", bound="InventoryItem")


@_attrs_define
class InventoryItem:
    """Base schema for products and materials with common inventory management features including tracking, supplier
    relationships, and variant configurations
    """

    id: int
    name: str
    type_: InventoryItemType
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    archived_at: None | Unset | datetime.datetime = UNSET
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    is_sellable: Unset | bool = UNSET
    default_supplier_id: None | Unset | int = UNSET
    additional_info: Unset | str = UNSET
    batch_tracked: Unset | bool = UNSET
    purchase_uom: None | Unset | str = UNSET
    purchase_uom_conversion_rate: None | Unset | float = UNSET
    custom_field_collection_id: None | Unset | int = UNSET
    variants: Unset | list["Variant"] = UNSET
    configs: Unset | list["ItemConfig"] = UNSET
    supplier: Union["Supplier", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.supplier import Supplier

        id = self.id

        name = self.name

        type_ = self.type_.value

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

        uom = self.uom

        category_name = self.category_name

        is_sellable = self.is_sellable

        default_supplier_id: None | Unset | int
        if isinstance(self.default_supplier_id, Unset):
            default_supplier_id = UNSET
        else:
            default_supplier_id = self.default_supplier_id

        additional_info = self.additional_info

        batch_tracked = self.batch_tracked

        purchase_uom: None | Unset | str
        if isinstance(self.purchase_uom, Unset):
            purchase_uom = UNSET
        else:
            purchase_uom = self.purchase_uom

        purchase_uom_conversion_rate: None | Unset | float
        if isinstance(self.purchase_uom_conversion_rate, Unset):
            purchase_uom_conversion_rate = UNSET
        else:
            purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        custom_field_collection_id: None | Unset | int
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

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

        supplier: None | Unset | dict[str, Any]
        if isinstance(self.supplier, Unset):
            supplier = UNSET
        elif isinstance(self.supplier, Supplier):
            supplier = self.supplier.to_dict()
        else:
            supplier = self.supplier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if archived_at is not UNSET:
            field_dict["archived_at"] = archived_at
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if default_supplier_id is not UNSET:
            field_dict["default_supplier_id"] = default_supplier_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if batch_tracked is not UNSET:
            field_dict["batch_tracked"] = batch_tracked
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id
        if variants is not UNSET:
            field_dict["variants"] = variants
        if configs is not UNSET:
            field_dict["configs"] = configs
        if supplier is not UNSET:
            field_dict["supplier"] = supplier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.item_config import ItemConfig
        from ..models.supplier import Supplier
        from ..models.variant import Variant

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        type_ = InventoryItemType(d.pop("type"))

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

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        def _parse_default_supplier_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        default_supplier_id = _parse_default_supplier_id(
            d.pop("default_supplier_id", UNSET)
        )

        additional_info = d.pop("additional_info", UNSET)

        batch_tracked = d.pop("batch_tracked", UNSET)

        def _parse_purchase_uom(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        purchase_uom = _parse_purchase_uom(d.pop("purchase_uom", UNSET))

        def _parse_purchase_uom_conversion_rate(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        purchase_uom_conversion_rate = _parse_purchase_uom_conversion_rate(
            d.pop("purchase_uom_conversion_rate", UNSET)
        )

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        variants = []
        _variants = d.pop("variants", UNSET)
        for variants_item_data in _variants or []:
            variants_item = Variant.from_dict(variants_item_data)

            variants.append(variants_item)

        configs = []
        _configs = d.pop("configs", UNSET)
        for configs_item_data in _configs or []:
            configs_item = ItemConfig.from_dict(configs_item_data)

            configs.append(configs_item)

        def _parse_supplier(data: object) -> Union["Supplier", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                supplier_type_0 = Supplier.from_dict(data)

                return supplier_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Supplier", None, Unset], data)

        supplier = _parse_supplier(d.pop("supplier", UNSET))

        inventory_item = cls(
            id=id,
            name=name,
            type_=type_,
            created_at=created_at,
            updated_at=updated_at,
            archived_at=archived_at,
            uom=uom,
            category_name=category_name,
            is_sellable=is_sellable,
            default_supplier_id=default_supplier_id,
            additional_info=additional_info,
            batch_tracked=batch_tracked,
            purchase_uom=purchase_uom,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            custom_field_collection_id=custom_field_collection_id,
            variants=variants,
            configs=configs,
            supplier=supplier,
        )

        inventory_item.additional_properties = d
        return inventory_item

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
