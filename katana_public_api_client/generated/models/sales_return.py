import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.sales_return_status import SalesReturnStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_return_row import SalesReturnRow


T = TypeVar("T", bound="SalesReturn")


@_attrs_define
class SalesReturn:
    id: int
    customer_id: int
    order_no: str
    return_location_id: int
    status: SalesReturnStatus
    sales_order_id: None | Unset | int = UNSET
    currency: Unset | str = UNSET
    return_date: None | Unset | datetime.datetime = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: None | Unset | str = UNSET
    refund_status: None | Unset | str = UNSET
    sales_return_rows: Unset | list["SalesReturnRow"] = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        customer_id = self.customer_id

        order_no = self.order_no

        return_location_id = self.return_location_id

        status = self.status.value

        sales_order_id: None | Unset | int
        if isinstance(self.sales_order_id, Unset):
            sales_order_id = UNSET
        else:
            sales_order_id = self.sales_order_id

        currency = self.currency

        return_date: None | Unset | str
        if isinstance(self.return_date, Unset):
            return_date = UNSET
        elif isinstance(self.return_date, datetime.datetime):
            return_date = self.return_date.isoformat()
        else:
            return_date = self.return_date

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        refund_status: None | Unset | str
        if isinstance(self.refund_status, Unset):
            refund_status = UNSET
        else:
            refund_status = self.refund_status

        sales_return_rows: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.sales_return_rows, Unset):
            sales_return_rows = []
            for sales_return_rows_item_data in self.sales_return_rows:
                sales_return_rows_item = sales_return_rows_item_data.to_dict()
                sales_return_rows.append(sales_return_rows_item)

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "customer_id": customer_id,
                "order_no": order_no,
                "return_location_id": return_location_id,
                "status": status,
            }
        )
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if return_date is not UNSET:
            field_dict["return_date"] = return_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if refund_status is not UNSET:
            field_dict["refund_status"] = refund_status
        if sales_return_rows is not UNSET:
            field_dict["sales_return_rows"] = sales_return_rows
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_return_row import SalesReturnRow

        d = dict(src_dict)
        id = d.pop("id")

        customer_id = d.pop("customer_id")

        order_no = d.pop("order_no")

        return_location_id = d.pop("return_location_id")

        status = SalesReturnStatus(d.pop("status"))

        def _parse_sales_order_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        sales_order_id = _parse_sales_order_id(d.pop("sales_order_id", UNSET))

        currency = d.pop("currency", UNSET)

        def _parse_return_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                return_date_type_0 = isoparse(data)

                return return_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        return_date = _parse_return_date(d.pop("return_date", UNSET))

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        def _parse_refund_status(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        refund_status = _parse_refund_status(d.pop("refund_status", UNSET))

        sales_return_rows = []
        _sales_return_rows = d.pop("sales_return_rows", UNSET)
        for sales_return_rows_item_data in _sales_return_rows or []:
            sales_return_rows_item = SalesReturnRow.from_dict(
                sales_return_rows_item_data
            )

            sales_return_rows.append(sales_return_rows_item)

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

        sales_return = cls(
            id=id,
            customer_id=customer_id,
            order_no=order_no,
            return_location_id=return_location_id,
            status=status,
            sales_order_id=sales_order_id,
            currency=currency,
            return_date=return_date,
            order_created_date=order_created_date,
            additional_info=additional_info,
            refund_status=refund_status,
            sales_return_rows=sales_return_rows,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        sales_return.additional_properties = d
        return sales_return

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
