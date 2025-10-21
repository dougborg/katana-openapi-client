from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_service_variant_request import CreateServiceVariantRequest


T = TypeVar("T", bound="CreateServiceRequest")


@_attrs_define
class CreateServiceRequest:
    """Request payload for creating a new service with variants and specifications

    Example:
        {'name': 'Assembly Service', 'uom': 'hours', 'category_name': 'Manufacturing Services', 'additional_info':
            'Professional product assembly service', 'is_sellable': True, 'custom_field_collection_id': 1, 'variants':
            [{'sku': 'ASSM-001', 'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}]}

    Attributes:
        name (str): The service's unique name
        variants (list['CreateServiceVariantRequest']): Array containing exactly one service variant object to create
        uom (Union[Unset, str]): The unit used to measure the quantity of the service (e.g. pcs, hours)
        category_name (Union[Unset, str]): A string used to group similar items for better organization and analysis
        additional_info (Union[Unset, str]): A string attached to the object to add any internal comments, links to
            external files, additional instructions, etc.
        is_sellable (Union[Unset, bool]): Sellable services can be added to Quotes and Sales orders
        custom_field_collection_id (Union[None, Unset, int]): ID of the custom field collection to associate with this
            service
    """

    name: str
    variants: list["CreateServiceVariantRequest"]
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    additional_info: Unset | str = UNSET
    is_sellable: Unset | bool = UNSET
    custom_field_collection_id: None | Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        variants = []
        for variants_item_data in self.variants:
            variants_item = variants_item_data.to_dict()
            variants.append(variants_item)

        uom = self.uom

        category_name = self.category_name

        additional_info = self.additional_info

        is_sellable = self.is_sellable

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
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_service_variant_request import CreateServiceVariantRequest

        d = dict(src_dict)
        name = d.pop("name")

        variants = []
        _variants = d.pop("variants")
        for variants_item_data in _variants:
            variants_item = CreateServiceVariantRequest.from_dict(variants_item_data)

            variants.append(variants_item)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        create_service_request = cls(
            name=name,
            variants=variants,
            uom=uom,
            category_name=category_name,
            additional_info=additional_info,
            is_sellable=is_sellable,
            custom_field_collection_id=custom_field_collection_id,
        )

        return create_service_request
