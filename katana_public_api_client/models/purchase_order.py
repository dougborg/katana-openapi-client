import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_row import PurchaseOrderRow
    from ..models.supplier import Supplier


T = TypeVar("T", bound="PurchaseOrder")


@_attrs_define
class PurchaseOrder:
    """Complete purchase order for procuring materials or products from suppliers, including order details, line items, and
    supplier information

        Example:
            {'id': 156, 'status': 'OPEN', 'order_no': 'PO-2024-0156', 'entity_type': 'regular', 'default_group_id': 1,
                'supplier_id': 4001, 'currency': 'USD', 'expected_arrival_date': '2024-02-15', 'order_created_date':
                '2024-01-28', 'additional_info': "Rush order - needed for Valentine's Day production run", 'location_id': 1,
                'tracking_location_id': None, 'total': 1962.5, 'total_in_base_currency': 1962.5, 'billing_status': 'UNBILLED',
                'last_document_status': 'CONFIRMED', 'ingredient_availability': 'AVAILABLE', 'ingredient_expected_date': None,
                'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z', 'deleted_at': None,
                'purchase_order_rows': [{'id': 501, 'quantity': 250, 'variant_id': 501, 'tax_rate_id': 1, 'price_per_unit':
                2.85, 'price_per_unit_in_base_currency': 2.85, 'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'kg',
                'currency': 'USD', 'conversion_rate': 1.0, 'total': 712.5, 'total_in_base_currency': 712.5, 'conversion_date':
                '2024-01-28T09:15:00Z', 'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z',
                'deleted_at': None}, {'id': 502, 'quantity': 100, 'variant_id': 502, 'tax_rate_id': 1, 'price_per_unit': 12.5,
                'price_per_unit_in_base_currency': 12.5, 'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces',
                'currency': 'USD', 'conversion_rate': 1.0, 'total': 1250.0, 'total_in_base_currency': 1250.0, 'conversion_date':
                '2024-01-28T09:15:00Z', 'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z',
                'deleted_at': None}], 'supplier': {'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email':
                'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen
                equipment and utensils', 'default_address_id': 4001, 'created_at': '2023-06-15T08:30:00Z', 'updated_at':
                '2024-01-15T14:20:00Z', 'deleted_at': None}}

        Attributes:
            created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
            updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
            deleted_at (Union[None, Unset, str]): Nullable deletion timestamp
            id (Union[Unset, int]): Unique identifier for the purchase order
            status (Union[Unset, str]): Current status of the purchase order (e.g., OPEN, RECEIVED, CLOSED)
            order_no (Union[Unset, str]): Unique purchase order number for tracking and reference
            entity_type (Union[Unset, str]): Type of purchase order - regular for materials or outsourced for subcontracted
                work
            default_group_id (Union[Unset, int]): Default grouping identifier for organizational purposes
            supplier_id (Union[Unset, int]): Unique identifier of the supplier providing the materials or services
            currency (Union[Unset, str]): Currency used for this purchase order (ISO 4217 format)
            expected_arrival_date (Union[Unset, str]): Expected date when the purchased items will arrive at the facility
            order_created_date (Union[Unset, str]): Date when the purchase order was created
            additional_info (Union[Unset, str]): Optional notes or special instructions for the supplier
            location_id (Union[Unset, int]): Primary location where the purchased items will be received and stored
            tracking_location_id (Union[None, Unset, int]): Optional tracking location for outsourced operations
            total (Union[Unset, float]): Total amount of the purchase order in the order currency
            total_in_base_currency (Union[Unset, float]): Total amount converted to the base currency
            billing_status (Union[Unset, str]): Current billing/payment status of the purchase order
            last_document_status (Union[Unset, str]): Status of the last document processed for this order
            ingredient_availability (Union[None, Unset, str]): Availability status of ingredients/materials in this order
            ingredient_expected_date (Union[None, Unset, str]): Expected date when all ingredients/materials will be
                available
            purchase_order_rows (Union[Unset, list['PurchaseOrderRow']]): List of line items in this purchase order
            supplier (Union[Unset, Supplier]): Supplier company or individual providing materials, products, or services for
                procurement operations Example: {'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email':
                'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen
                equipment and utensils. Reliable delivery times.', 'default_address_id': 4001, 'created_at':
                '2023-06-15T08:30:00Z', 'updated_at': '2024-01-15T14:20:00Z', 'deleted_at': None, 'addresses': [{'id': 4001,
                'company': 'Premium Kitchen Supplies Ltd', 'street': '1250 Industrial Blvd', 'street2': 'Suite 200', 'city':
                'Chicago', 'state': 'IL', 'zip': '60601', 'country': 'US', 'created_at': '2023-06-15T08:30:00Z', 'updated_at':
                '2023-06-15T08:30:00Z', 'deleted_at': None}]}.
    """

    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | str = UNSET
    id: Unset | int = UNSET
    status: Unset | str = UNSET
    order_no: Unset | str = UNSET
    entity_type: Unset | str = UNSET
    default_group_id: Unset | int = UNSET
    supplier_id: Unset | int = UNSET
    currency: Unset | str = UNSET
    expected_arrival_date: Unset | str = UNSET
    order_created_date: Unset | str = UNSET
    additional_info: Unset | str = UNSET
    location_id: Unset | int = UNSET
    tracking_location_id: None | Unset | int = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    billing_status: Unset | str = UNSET
    last_document_status: Unset | str = UNSET
    ingredient_availability: None | Unset | str = UNSET
    ingredient_expected_date: None | Unset | str = UNSET
    purchase_order_rows: Unset | list["PurchaseOrderRow"] = UNSET
    supplier: Union[Unset, "Supplier"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = self.deleted_at

        id = self.id

        status = self.status

        order_no = self.order_no

        entity_type = self.entity_type

        default_group_id = self.default_group_id

        supplier_id = self.supplier_id

        currency = self.currency

        expected_arrival_date = self.expected_arrival_date

        order_created_date = self.order_created_date

        additional_info = self.additional_info

        location_id = self.location_id

        tracking_location_id: None | Unset | int
        if isinstance(self.tracking_location_id, Unset):
            tracking_location_id = UNSET
        else:
            tracking_location_id = self.tracking_location_id

        total = self.total

        total_in_base_currency = self.total_in_base_currency

        billing_status = self.billing_status

        last_document_status = self.last_document_status

        ingredient_availability: None | Unset | str
        if isinstance(self.ingredient_availability, Unset):
            ingredient_availability = UNSET
        else:
            ingredient_availability = self.ingredient_availability

        ingredient_expected_date: None | Unset | str
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        else:
            ingredient_expected_date = self.ingredient_expected_date

        purchase_order_rows: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.purchase_order_rows, Unset):
            purchase_order_rows = []
            for purchase_order_rows_item_data in self.purchase_order_rows:
                purchase_order_rows_item = purchase_order_rows_item_data.to_dict()
                purchase_order_rows.append(purchase_order_rows_item)

        supplier: Unset | dict[str, Any] = UNSET
        if not isinstance(self.supplier, Unset):
            supplier = self.supplier.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if default_group_id is not UNSET:
            field_dict["default_group_id"] = default_group_id
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if tracking_location_id is not UNSET:
            field_dict["tracking_location_id"] = tracking_location_id
        if total is not UNSET:
            field_dict["total"] = total
        if total_in_base_currency is not UNSET:
            field_dict["total_in_base_currency"] = total_in_base_currency
        if billing_status is not UNSET:
            field_dict["billing_status"] = billing_status
        if last_document_status is not UNSET:
            field_dict["last_document_status"] = last_document_status
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date
        if purchase_order_rows is not UNSET:
            field_dict["purchase_order_rows"] = purchase_order_rows
        if supplier is not UNSET:
            field_dict["supplier"] = supplier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_row import PurchaseOrderRow
        from ..models.supplier import Supplier

        d = dict(src_dict)
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

        def _parse_deleted_at(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        id = d.pop("id", UNSET)

        status = d.pop("status", UNSET)

        order_no = d.pop("order_no", UNSET)

        entity_type = d.pop("entity_type", UNSET)

        default_group_id = d.pop("default_group_id", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        currency = d.pop("currency", UNSET)

        expected_arrival_date = d.pop("expected_arrival_date", UNSET)

        order_created_date = d.pop("order_created_date", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        location_id = d.pop("location_id", UNSET)

        def _parse_tracking_location_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        tracking_location_id = _parse_tracking_location_id(
            d.pop("tracking_location_id", UNSET)
        )

        total = d.pop("total", UNSET)

        total_in_base_currency = d.pop("total_in_base_currency", UNSET)

        billing_status = d.pop("billing_status", UNSET)

        last_document_status = d.pop("last_document_status", UNSET)

        def _parse_ingredient_availability(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        ingredient_availability = _parse_ingredient_availability(
            d.pop("ingredient_availability", UNSET)
        )

        def _parse_ingredient_expected_date(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        ingredient_expected_date = _parse_ingredient_expected_date(
            d.pop("ingredient_expected_date", UNSET)
        )

        purchase_order_rows = []
        _purchase_order_rows = d.pop("purchase_order_rows", UNSET)
        for purchase_order_rows_item_data in _purchase_order_rows or []:
            purchase_order_rows_item = PurchaseOrderRow.from_dict(
                purchase_order_rows_item_data
            )

            purchase_order_rows.append(purchase_order_rows_item)

        _supplier = d.pop("supplier", UNSET)
        supplier: Unset | Supplier
        if isinstance(_supplier, Unset):
            supplier = UNSET
        else:
            supplier = Supplier.from_dict(_supplier)

        purchase_order = cls(
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            id=id,
            status=status,
            order_no=order_no,
            entity_type=entity_type,
            default_group_id=default_group_id,
            supplier_id=supplier_id,
            currency=currency,
            expected_arrival_date=expected_arrival_date,
            order_created_date=order_created_date,
            additional_info=additional_info,
            location_id=location_id,
            tracking_location_id=tracking_location_id,
            total=total,
            total_in_base_currency=total_in_base_currency,
            billing_status=billing_status,
            last_document_status=last_document_status,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
            purchase_order_rows=purchase_order_rows,
            supplier=supplier,
        )

        purchase_order.additional_properties = d
        return purchase_order

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
