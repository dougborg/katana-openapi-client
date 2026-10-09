from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_service_variant_request_custom_fields_item import (
        CreateServiceVariantRequestCustomFieldsItem,
    )
    from ..models.create_service_variant_request_custom_fields_type_1 import (
        CreateServiceVariantRequestCustomFieldsType1,
    )


T = TypeVar("T", bound="CreateServiceVariantRequest")


@_attrs_define
class CreateServiceVariantRequest:
    """Request payload for creating a service variant with pricing and custom fields

    Example:
        {'sku': 'ASSM-001', 'sales_price': 75.0, 'default_cost': 50.0, 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}]}
    """

    sku: str | Unset = UNSET
    sales_price: float | Unset | None = UNSET
    default_cost: float | Unset | None = UNSET
    custom_fields: (
        CreateServiceVariantRequestCustomFieldsType1
        | list[CreateServiceVariantRequestCustomFieldsItem]
        | Unset
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        sku = self.sku

        sales_price: float | Unset | None
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        else:
            sales_price = self.sales_price

        default_cost: float | Unset | None
        if isinstance(self.default_cost, Unset):
            default_cost = UNSET
        else:
            default_cost = self.default_cost

        custom_fields: dict[str, Any] | list[dict[str, Any]] | Unset
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(self.custom_fields, list):
            custom_fields = []
            for custom_fields_type_0_item_data in self.custom_fields:
                custom_fields_type_0_item = custom_fields_type_0_item_data.to_dict()
                custom_fields.append(custom_fields_type_0_item)

        else:
            custom_fields = self.custom_fields.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if sku is not UNSET:
            field_dict["sku"] = sku
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
        from ..models.create_service_variant_request_custom_fields_type_1 import (
            CreateServiceVariantRequestCustomFieldsType1,
        )

        d = dict(src_dict)
        sku = d.pop("sku", UNSET)

        def _parse_sales_price(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_default_cost(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        default_cost = _parse_default_cost(d.pop("default_cost", UNSET))

        def _parse_custom_fields(
            data: object,
        ) -> (
            CreateServiceVariantRequestCustomFieldsType1
            | list[CreateServiceVariantRequestCustomFieldsItem]
            | Unset
        ):
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                custom_fields_type_0 = []
                _custom_fields_type_0 = data
                for custom_fields_type_0_item_data in _custom_fields_type_0:
                    custom_fields_type_0_item = (
                        CreateServiceVariantRequestCustomFieldsItem.from_dict(
                            cast(Mapping[str, Any], custom_fields_type_0_item_data)
                        )
                    )

                    custom_fields_type_0.append(custom_fields_type_0_item)

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            custom_fields_type_1 = (
                CreateServiceVariantRequestCustomFieldsType1.from_dict(
                    cast(Mapping[str, Any], data)
                )
            )

            return custom_fields_type_1

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        create_service_variant_request = cls(
            sku=sku,
            sales_price=sales_price,
            default_cost=default_cost,
            custom_fields=custom_fields,
        )

        return create_service_variant_request
