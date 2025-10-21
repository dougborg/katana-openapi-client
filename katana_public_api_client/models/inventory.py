from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deletable_entity import DeletableEntity
    from ..models.location_type_0 import LocationType0
    from ..models.variant import Variant


T = TypeVar("T", bound="Inventory")


@_attrs_define
class Inventory:
    """Represents the current inventory state for a specific product variant at a location.
    Includes stock levels, commitments, expectations, and financial information.

        Example:
            {'variant_id': 3001, 'location_id': 1, 'safety_stock_level': '25.0', 'reorder_point': '25.0', 'average_cost':
                '15.50', 'value_in_stock': '2325.00', 'quantity_in_stock': '150.0', 'quantity_committed': '25.0',
                'quantity_expected': '50.0', 'quantity_missing_or_excess': '0.0', 'quantity_potential': '175.0'}

        Attributes:
            variant_id (int): Unique identifier of the product variant
            location_id (int): Unique identifier of the location where inventory is stored
            reorder_point (str): (Deprecated - use safety_stock_level instead) Queries the safety stock level
            average_cost (str): Average cost per unit of this variant at this location
            value_in_stock (str): Total monetary value of current stock
            quantity_in_stock (str): Current physical quantity available at this location
            quantity_committed (str): Quantity already allocated to orders but not yet shipped
            quantity_expected (str): Quantity expected to arrive from pending purchase orders
            quantity_missing_or_excess (str): Difference between expected and actual stock (negative means missing, positive
                means excess)
            quantity_potential (str): Total quantity that could be available (in stock + expected)
            safety_stock_level (Union[Unset, str]): The quantity of a product or material which indicates an acceptable
                stock level for unexpected demand without overstocking
            variant (Union[Unset, Variant]): Specific SKU of a product or material with unique pricing, configuration, and
                inventory tracking Example: {'id': 3001, 'sku': 'KNF-PRO-8PC-STL', 'sales_price': 299.99, 'product_id': 101,
                'material_id': None, 'purchase_price': 150.0, 'product_or_material_name': 'Professional Kitchen Knife Set -
                8-Piece - Steel Handles', 'type': 'product', 'internal_barcode': 'INT-KNF-001', 'registered_barcode':
                '789123456789', 'supplier_item_codes': ['SUP-KNF-8PC-001'], 'lead_time': 7, 'minimum_order_quantity': 1,
                'custom_fields': [{'field_name': 'Warranty Period', 'field_value': '5 years'}], 'config_attributes':
                [{'config_name': 'Piece Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
                'Steel'}], 'created_at': '2024-01-15T08:00:00.000Z', 'updated_at': '2024-08-20T14:45:00.000Z', 'deleted_at':
                None}.
            location (Union['DeletableEntity', 'LocationType0', Unset]): Manufacturing location or warehouse facility where
                inventory is managed and operations are performed Example: {'data': [{'id': 1, 'name': 'Main location',
                'legal_name': 'Amazon', 'address_id': 1, 'address': {'id': 1, 'city': 'New York', 'country': 'US', 'line_1': '10
                East 20th Example St', 'line_2': '', 'state': 'New York', 'zip': '10000'}, 'is_primary': True, 'sales_allowed':
                True, 'purchase_allowed': True, 'manufacturing_allowed': True, 'created_at': '2020-10-23T10:37:05.085Z',
                'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None}, {'id': 2, 'name': 'Secondary location',
                'legal_name': 'Amazon', 'address_id': None, 'address': None, 'is_primary': False, 'sales_allowed': False,
                'purchase_allowed': True, 'manufacturing_allowed': False, 'created_at': '2020-10-23T10:37:05.085Z',
                'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None}]}.
    """

    variant_id: int
    location_id: int
    reorder_point: str
    average_cost: str
    value_in_stock: str
    quantity_in_stock: str
    quantity_committed: str
    quantity_expected: str
    quantity_missing_or_excess: str
    quantity_potential: str
    safety_stock_level: Unset | str = UNSET
    variant: Union[Unset, "Variant"] = UNSET
    location: Union["DeletableEntity", "LocationType0", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.location_type_0 import LocationType0

        variant_id = self.variant_id

        location_id = self.location_id

        reorder_point = self.reorder_point

        average_cost = self.average_cost

        value_in_stock = self.value_in_stock

        quantity_in_stock = self.quantity_in_stock

        quantity_committed = self.quantity_committed

        quantity_expected = self.quantity_expected

        quantity_missing_or_excess = self.quantity_missing_or_excess

        quantity_potential = self.quantity_potential

        safety_stock_level = self.safety_stock_level

        variant: Unset | dict[str, Any] = UNSET
        if not isinstance(self.variant, Unset):
            variant = self.variant.to_dict()

        location: Unset | dict[str, Any]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, LocationType0):
            location = self.location.to_dict()
        else:
            location = self.location.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "reorder_point": reorder_point,
                "average_cost": average_cost,
                "value_in_stock": value_in_stock,
                "quantity_in_stock": quantity_in_stock,
                "quantity_committed": quantity_committed,
                "quantity_expected": quantity_expected,
                "quantity_missing_or_excess": quantity_missing_or_excess,
                "quantity_potential": quantity_potential,
            }
        )
        if safety_stock_level is not UNSET:
            field_dict["safety_stock_level"] = safety_stock_level
        if variant is not UNSET:
            field_dict["variant"] = variant
        if location is not UNSET:
            field_dict["location"] = location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deletable_entity import DeletableEntity
        from ..models.location_type_0 import LocationType0
        from ..models.variant import Variant

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        reorder_point = d.pop("reorder_point")

        average_cost = d.pop("average_cost")

        value_in_stock = d.pop("value_in_stock")

        quantity_in_stock = d.pop("quantity_in_stock")

        quantity_committed = d.pop("quantity_committed")

        quantity_expected = d.pop("quantity_expected")

        quantity_missing_or_excess = d.pop("quantity_missing_or_excess")

        quantity_potential = d.pop("quantity_potential")

        safety_stock_level = d.pop("safety_stock_level", UNSET)

        _variant = d.pop("variant", UNSET)
        variant: Unset | Variant
        if isinstance(_variant, Unset):
            variant = UNSET
        else:
            variant = Variant.from_dict(_variant)

        def _parse_location(
            data: object,
        ) -> Union["DeletableEntity", "LocationType0", Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_location_type_0 = LocationType0.from_dict(data)

                return componentsschemas_location_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_location_type_1 = DeletableEntity.from_dict(data)

            return componentsschemas_location_type_1

        location = _parse_location(d.pop("location", UNSET))

        inventory = cls(
            variant_id=variant_id,
            location_id=location_id,
            reorder_point=reorder_point,
            average_cost=average_cost,
            value_in_stock=value_in_stock,
            quantity_in_stock=quantity_in_stock,
            quantity_committed=quantity_committed,
            quantity_expected=quantity_expected,
            quantity_missing_or_excess=quantity_missing_or_excess,
            quantity_potential=quantity_potential,
            safety_stock_level=safety_stock_level,
            variant=variant,
            location=location,
        )

        inventory.additional_properties = d
        return inventory

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
