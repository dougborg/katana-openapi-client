from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_service_variant_request_custom_fields_item import (
        CreateServiceVariantRequestCustomFieldsItem,
    )


T = TypeVar("T", bound="CreateServiceVariantRequest")


@_attrs_define
class CreateServiceVariantRequest:
    """Request payload for creating a service variant with pricing and custom fields

    Example:
        {'sku': 'ASSM-001', 'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}

    Attributes:
        sku (str): A unique service code
        sales_price (Union[None, Unset, float]): Default sales price (excluding tax)
        default_cost (Union[None, Unset, float]): Default cost which is used to calculate profit
        custom_fields (Union[Unset, list['CreateServiceVariantRequestCustomFieldsItem']]): Custom field values for this
            variant
    """

    sku: str
    sales_price: None | Unset | float = UNSET
    default_cost: None | Unset | float = UNSET
    custom_fields: Unset | list["CreateServiceVariantRequestCustomFieldsItem"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        sku = self.sku

        sales_price: None | Unset | float
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        else:
            sales_price = self.sales_price

        default_cost: None | Unset | float
        if isinstance(self.default_cost, Unset):
            default_cost = UNSET
        else:
            default_cost = self.default_cost

        custom_fields: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.custom_fields, Unset):
            custom_fields = []
            for custom_fields_item_data in self.custom_fields:
                custom_fields_item = custom_fields_item_data.to_dict()
                custom_fields.append(custom_fields_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sku": sku,
            }
        )
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if default_cost is not UNSET:
            field_dict["default_cost"] = default_cost
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_service_variant_request_custom_fields_item import (
            CreateServiceVariantRequestCustomFieldsItem,
        )

        d = dict(src_dict)
        sku = d.pop("sku")

        def _parse_sales_price(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_default_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        default_cost = _parse_default_cost(d.pop("default_cost", UNSET))

        custom_fields = []
        _custom_fields = d.pop("custom_fields", UNSET)
        for custom_fields_item_data in _custom_fields or []:
            custom_fields_item = CreateServiceVariantRequestCustomFieldsItem.from_dict(
                custom_fields_item_data
            )

            custom_fields.append(custom_fields_item)

        create_service_variant_request = cls(
            sku=sku,
            sales_price=sales_price,
            default_cost=default_cost,
            custom_fields=custom_fields,
        )

        return create_service_variant_request
