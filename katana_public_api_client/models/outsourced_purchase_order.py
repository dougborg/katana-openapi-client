import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.outsourced_purchase_order_entity_type import (
    OutsourcedPurchaseOrderEntityType,
)
from ..models.outsourced_purchase_order_ingredient_availability import (
    OutsourcedPurchaseOrderIngredientAvailability,
)
from ..models.purchase_order_base_billing_status import PurchaseOrderBaseBillingStatus
from ..models.purchase_order_base_last_document_status import (
    PurchaseOrderBaseLastDocumentStatus,
)
from ..models.purchase_order_base_status import PurchaseOrderBaseStatus

if TYPE_CHECKING:
    from ..models.purchase_order_row import PurchaseOrderRow
    from ..models.supplier import Supplier


T = TypeVar("T", bound="OutsourcedPurchaseOrder")


@_attrs_define
class OutsourcedPurchaseOrder:
    """Outsourced purchase order for subcontracted manufacturing

    Attributes:
        id (int): Unique identifier
        tracking_location_id (int): The ID location where the ingredients on the outsourced purchase order are processed
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
        status (Union[Unset, PurchaseOrderBaseStatus]): Status of the order.
        order_no (Union[Unset, str]): A unique, identifying string used in the UI and controlled by the user.
        entity_type (Union[Unset, OutsourcedPurchaseOrderEntityType]): Purchase order type identifier
        default_group_id (Union[Unset, int]): Default grouping identifier for organizational purposes
        supplier_id (Union[Unset, int]): ID of the supplier who this order belongs to.
        currency (Union[Unset, str]): Currency of the purchase order. Filled with supplier currency by default.
        expected_arrival_date (Union[Unset, datetime.datetime]): The timestamp when the items are expected to arrive (in
            full) in your warehouse.
        order_created_date (Union[Unset, datetime.datetime]): The timestamp of creating the document.
        additional_info (Union[Unset, str]): A string attached to the object to add any internal comments, links to
            external files, additional instructions, etc.
        location_id (Union[Unset, int]): The ID of the location to which items are received.
        total (Union[Unset, float]): The total value of the order (including taxes) in purchase order currency.
        total_in_base_currency (Union[Unset, float]): The total value of the order (including taxes) in base currency.
        billing_status (Union[Unset, PurchaseOrderBaseBillingStatus]): Indicating the status of generating the bill
            through accounting integration to either Xero or QuickBooks Online. "PARTIALLY_BILLED" does not apply to Xero
            integration.
        last_document_status (Union[Unset, PurchaseOrderBaseLastDocumentStatus]): Status of the last e-mail sent from
            (O)PO card.
        purchase_order_rows (Union[Unset, list['PurchaseOrderRow']]): List of line items in this purchase order
        supplier (Union[Unset, Supplier]): Supplier company or individual providing materials, products, or services for
            procurement operations Example: {'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email':
            'orders@premiumkitchen.com', 'phone': '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen
            equipment and utensils. Reliable delivery times.', 'default_address_id': 4001, 'created_at':
            '2023-06-15T08:30:00Z', 'updated_at': '2024-01-15T14:20:00Z', 'deleted_at': None, 'addresses': [{'id': 4001,
            'company': 'Premium Kitchen Supplies Ltd', 'street': '1250 Industrial Blvd', 'street2': 'Suite 200', 'city':
            'Chicago', 'state': 'IL', 'zip': '60601', 'country': 'US', 'created_at': '2023-06-15T08:30:00Z', 'updated_at':
            '2023-06-15T08:30:00Z', 'deleted_at': None}]}.
        ingredient_availability (Union[Unset, OutsourcedPurchaseOrderIngredientAvailability]): Status of ingredients
            required for outsourced purchase order production
        ingredient_expected_date (Union[None, Unset, datetime.datetime]): The latest date of a manufacturing order
            production deadline or a purchasing order expected arrival date that relates to the required ingredient
    """

    id: int
    tracking_location_id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    status: Unset | PurchaseOrderBaseStatus = UNSET
    order_no: Unset | str = UNSET
    entity_type: Unset | OutsourcedPurchaseOrderEntityType = UNSET
    default_group_id: Unset | int = UNSET
    supplier_id: Unset | int = UNSET
    currency: Unset | str = UNSET
    expected_arrival_date: Unset | datetime.datetime = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    location_id: Unset | int = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    billing_status: Unset | PurchaseOrderBaseBillingStatus = UNSET
    last_document_status: Unset | PurchaseOrderBaseLastDocumentStatus = UNSET
    purchase_order_rows: Unset | list["PurchaseOrderRow"] = UNSET
    supplier: Union[Unset, "Supplier"] = UNSET
    ingredient_availability: Unset | OutsourcedPurchaseOrderIngredientAvailability = (
        UNSET
    )
    ingredient_expected_date: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        tracking_location_id = self.tracking_location_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        order_no = self.order_no

        entity_type: Unset | str = UNSET
        if not isinstance(self.entity_type, Unset):
            entity_type = self.entity_type.value

        default_group_id = self.default_group_id

        supplier_id = self.supplier_id

        currency = self.currency

        expected_arrival_date: Unset | str = UNSET
        if not isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = self.expected_arrival_date.isoformat()

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info = self.additional_info

        location_id = self.location_id

        total = self.total

        total_in_base_currency = self.total_in_base_currency

        billing_status: Unset | str = UNSET
        if not isinstance(self.billing_status, Unset):
            billing_status = self.billing_status.value

        last_document_status: Unset | str = UNSET
        if not isinstance(self.last_document_status, Unset):
            last_document_status = self.last_document_status.value

        purchase_order_rows: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.purchase_order_rows, Unset):
            purchase_order_rows = []
            for purchase_order_rows_item_data in self.purchase_order_rows:
                purchase_order_rows_item = purchase_order_rows_item_data.to_dict()
                purchase_order_rows.append(purchase_order_rows_item)

        supplier: Unset | dict[str, Any] = UNSET
        if not isinstance(self.supplier, Unset):
            supplier = self.supplier.to_dict()

        ingredient_availability: Unset | str = UNSET
        if not isinstance(self.ingredient_availability, Unset):
            ingredient_availability = self.ingredient_availability.value

        ingredient_expected_date: None | Unset | str
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        elif isinstance(self.ingredient_expected_date, datetime.datetime):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()
        else:
            ingredient_expected_date = self.ingredient_expected_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tracking_location_id": tracking_location_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
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
        if total is not UNSET:
            field_dict["total"] = total
        if total_in_base_currency is not UNSET:
            field_dict["total_in_base_currency"] = total_in_base_currency
        if billing_status is not UNSET:
            field_dict["billing_status"] = billing_status
        if last_document_status is not UNSET:
            field_dict["last_document_status"] = last_document_status
        if purchase_order_rows is not UNSET:
            field_dict["purchase_order_rows"] = purchase_order_rows
        if supplier is not UNSET:
            field_dict["supplier"] = supplier
        if ingredient_availability is not UNSET:
            field_dict["ingredient_availability"] = ingredient_availability
        if ingredient_expected_date is not UNSET:
            field_dict["ingredient_expected_date"] = ingredient_expected_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_row import PurchaseOrderRow
        from ..models.supplier import Supplier

        d = dict(src_dict)
        id = d.pop("id")

        tracking_location_id = d.pop("tracking_location_id")

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        _status = d.pop("status", UNSET)
        status: Unset | PurchaseOrderBaseStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = PurchaseOrderBaseStatus(_status)

        order_no = d.pop("order_no", UNSET)

        _entity_type = d.pop("entity_type", UNSET)
        entity_type: Unset | OutsourcedPurchaseOrderEntityType
        if isinstance(_entity_type, Unset):
            entity_type = UNSET
        else:
            entity_type = OutsourcedPurchaseOrderEntityType(_entity_type)

        default_group_id = d.pop("default_group_id", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        currency = d.pop("currency", UNSET)

        _expected_arrival_date = d.pop("expected_arrival_date", UNSET)
        expected_arrival_date: Unset | datetime.datetime
        if isinstance(_expected_arrival_date, Unset):
            expected_arrival_date = UNSET
        else:
            expected_arrival_date = isoparse(_expected_arrival_date)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        additional_info = d.pop("additional_info", UNSET)

        location_id = d.pop("location_id", UNSET)

        total = d.pop("total", UNSET)

        total_in_base_currency = d.pop("total_in_base_currency", UNSET)

        _billing_status = d.pop("billing_status", UNSET)
        billing_status: Unset | PurchaseOrderBaseBillingStatus
        if isinstance(_billing_status, Unset):
            billing_status = UNSET
        else:
            billing_status = PurchaseOrderBaseBillingStatus(_billing_status)

        _last_document_status = d.pop("last_document_status", UNSET)
        last_document_status: Unset | PurchaseOrderBaseLastDocumentStatus
        if isinstance(_last_document_status, Unset):
            last_document_status = UNSET
        else:
            last_document_status = PurchaseOrderBaseLastDocumentStatus(
                _last_document_status
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

        _ingredient_availability = d.pop("ingredient_availability", UNSET)
        ingredient_availability: Unset | OutsourcedPurchaseOrderIngredientAvailability
        if isinstance(_ingredient_availability, Unset):
            ingredient_availability = UNSET
        else:
            ingredient_availability = OutsourcedPurchaseOrderIngredientAvailability(
                _ingredient_availability
            )

        def _parse_ingredient_expected_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_expected_date_type_0 = isoparse(data)

                return ingredient_expected_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        ingredient_expected_date = _parse_ingredient_expected_date(
            d.pop("ingredient_expected_date", UNSET)
        )

        outsourced_purchase_order = cls(
            id=id,
            tracking_location_id=tracking_location_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
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
            total=total,
            total_in_base_currency=total_in_base_currency,
            billing_status=billing_status,
            last_document_status=last_document_status,
            purchase_order_rows=purchase_order_rows,
            supplier=supplier,
            ingredient_availability=ingredient_availability,
            ingredient_expected_date=ingredient_expected_date,
        )

        outsourced_purchase_order.additional_properties = d
        return outsourced_purchase_order

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
