import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.purchase_order_billing_status import PurchaseOrderBillingStatus
from ..models.purchase_order_entity_type import PurchaseOrderEntityType
from ..models.purchase_order_ingredient_availability_type_1 import (
    PurchaseOrderIngredientAvailabilityType1,
)
from ..models.purchase_order_ingredient_availability_type_2_type_1 import (
    PurchaseOrderIngredientAvailabilityType2Type1,
)
from ..models.purchase_order_ingredient_availability_type_3_type_1 import (
    PurchaseOrderIngredientAvailabilityType3Type1,
)
from ..models.purchase_order_last_document_status import PurchaseOrderLastDocumentStatus
from ..models.purchase_order_status import PurchaseOrderStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_row import PurchaseOrderRow
    from ..models.supplier import Supplier


T = TypeVar("T", bound="PurchaseOrder")


@_attrs_define
class PurchaseOrder:
    """A purchase order represents a formal request to purchase materials or products from a supplier, including pricing,
    quantities, and delivery terms
    """

    id: int
    status: PurchaseOrderStatus
    order_no: str
    supplier_id: int
    currency: str
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    entity_type: Unset | PurchaseOrderEntityType = UNSET
    default_group_id: Unset | int = UNSET
    expected_arrival_date: Unset | datetime.datetime = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    location_id: Unset | int = UNSET
    tracking_location_id: None | Unset | int = UNSET
    total: Unset | float = UNSET
    total_in_base_currency: Unset | float = UNSET
    billing_status: Unset | PurchaseOrderBillingStatus = UNSET
    last_document_status: Unset | PurchaseOrderLastDocumentStatus = UNSET
    ingredient_availability: (
        None
        | PurchaseOrderIngredientAvailabilityType1
        | PurchaseOrderIngredientAvailabilityType2Type1
        | PurchaseOrderIngredientAvailabilityType3Type1
        | Unset
    ) = UNSET
    ingredient_expected_date: None | Unset | datetime.datetime = UNSET
    purchase_order_rows: Unset | list["PurchaseOrderRow"] = UNSET
    supplier: Union[Unset, "Supplier"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status = self.status.value

        order_no = self.order_no

        supplier_id = self.supplier_id

        currency = self.currency

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

        entity_type: Unset | str = UNSET
        if not isinstance(self.entity_type, Unset):
            entity_type = self.entity_type.value

        default_group_id = self.default_group_id

        expected_arrival_date: Unset | str = UNSET
        if not isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = self.expected_arrival_date.isoformat()

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info = self.additional_info

        location_id = self.location_id

        tracking_location_id: None | Unset | int
        if isinstance(self.tracking_location_id, Unset):
            tracking_location_id = UNSET
        else:
            tracking_location_id = self.tracking_location_id

        total = self.total

        total_in_base_currency = self.total_in_base_currency

        billing_status: Unset | str = UNSET
        if not isinstance(self.billing_status, Unset):
            billing_status = self.billing_status.value

        last_document_status: Unset | str = UNSET
        if not isinstance(self.last_document_status, Unset):
            last_document_status = self.last_document_status.value

        ingredient_availability: None | Unset | str
        if isinstance(self.ingredient_availability, Unset):
            ingredient_availability = UNSET
        elif isinstance(
            self.ingredient_availability,
            PurchaseOrderIngredientAvailabilityType1
            | PurchaseOrderIngredientAvailabilityType2Type1
            | PurchaseOrderIngredientAvailabilityType3Type1,
        ):
            ingredient_availability = self.ingredient_availability.value
        else:
            ingredient_availability = self.ingredient_availability

        ingredient_expected_date: None | Unset | str
        if isinstance(self.ingredient_expected_date, Unset):
            ingredient_expected_date = UNSET
        elif isinstance(self.ingredient_expected_date, datetime.datetime):
            ingredient_expected_date = self.ingredient_expected_date.isoformat()
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
        field_dict.update(
            {
                "id": id,
                "status": status,
                "order_no": order_no,
                "supplier_id": supplier_id,
                "currency": currency,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if default_group_id is not UNSET:
            field_dict["default_group_id"] = default_group_id
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
        id = d.pop("id")

        status = PurchaseOrderStatus(d.pop("status"))

        order_no = d.pop("order_no")

        supplier_id = d.pop("supplier_id")

        currency = d.pop("currency")

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

        _entity_type = d.pop("entity_type", UNSET)
        entity_type: Unset | PurchaseOrderEntityType
        if isinstance(_entity_type, Unset):
            entity_type = UNSET
        else:
            entity_type = PurchaseOrderEntityType(_entity_type)

        default_group_id = d.pop("default_group_id", UNSET)

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

        _billing_status = d.pop("billing_status", UNSET)
        billing_status: Unset | PurchaseOrderBillingStatus
        if isinstance(_billing_status, Unset):
            billing_status = UNSET
        else:
            billing_status = PurchaseOrderBillingStatus(_billing_status)

        _last_document_status = d.pop("last_document_status", UNSET)
        last_document_status: Unset | PurchaseOrderLastDocumentStatus
        if isinstance(_last_document_status, Unset):
            last_document_status = UNSET
        else:
            last_document_status = PurchaseOrderLastDocumentStatus(
                _last_document_status
            )

        def _parse_ingredient_availability(
            data: object,
        ) -> (
            None
            | PurchaseOrderIngredientAvailabilityType1
            | PurchaseOrderIngredientAvailabilityType2Type1
            | PurchaseOrderIngredientAvailabilityType3Type1
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_availability_type_1 = (
                    PurchaseOrderIngredientAvailabilityType1(data)
                )

                return ingredient_availability_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_availability_type_2_type_1 = (
                    PurchaseOrderIngredientAvailabilityType2Type1(data)
                )

                return ingredient_availability_type_2_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ingredient_availability_type_3_type_1 = (
                    PurchaseOrderIngredientAvailabilityType3Type1(data)
                )

                return ingredient_availability_type_3_type_1
            except:  # noqa: E722
                pass
            return cast(
                None
                | PurchaseOrderIngredientAvailabilityType1
                | PurchaseOrderIngredientAvailabilityType2Type1
                | PurchaseOrderIngredientAvailabilityType3Type1
                | Unset,
                data,
            )

        ingredient_availability = _parse_ingredient_availability(
            d.pop("ingredient_availability", UNSET)
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
            id=id,
            status=status,
            order_no=order_no,
            supplier_id=supplier_id,
            currency=currency,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            entity_type=entity_type,
            default_group_id=default_group_id,
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
