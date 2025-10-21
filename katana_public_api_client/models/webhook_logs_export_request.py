import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.webhook_logs_export_request_format import WebhookLogsExportRequestFormat
from ..models.webhook_logs_export_request_status_filter_item import (
    WebhookLogsExportRequestStatusFilterItem,
)

T = TypeVar("T", bound="WebhookLogsExportRequest")


@_attrs_define
class WebhookLogsExportRequest:
    """Request parameters for exporting webhook delivery logs for analysis and debugging

    Example:
        {'webhook_id': 1, 'start_date': '2024-01-10T00:00:00Z', 'end_date': '2024-01-15T23:59:59Z', 'status_filter':
            ['failure', 'retry'], 'format': 'csv'}

    Attributes:
        webhook_id (Union[Unset, int]): Filter logs to specific webhook subscription (optional - if not provided,
            exports all webhook logs)
        start_date (Union[Unset, datetime.datetime]): Start date for log export range (ISO 8601 format)
        end_date (Union[Unset, datetime.datetime]): End date for log export range (ISO 8601 format)
        status_filter (Union[Unset, list[WebhookLogsExportRequestStatusFilterItem]]): Filter logs by delivery status
            (success, failure, retry)
        format_ (Union[Unset, WebhookLogsExportRequestFormat]): Export file format preference Default:
            WebhookLogsExportRequestFormat.CSV.
    """

    webhook_id: Unset | int = UNSET
    start_date: Unset | datetime.datetime = UNSET
    end_date: Unset | datetime.datetime = UNSET
    status_filter: Unset | list[WebhookLogsExportRequestStatusFilterItem] = UNSET
    format_: Unset | WebhookLogsExportRequestFormat = WebhookLogsExportRequestFormat.CSV

    def to_dict(self) -> dict[str, Any]:
        webhook_id = self.webhook_id

        start_date: Unset | str = UNSET
        if not isinstance(self.start_date, Unset):
            start_date = self.start_date.isoformat()

        end_date: Unset | str = UNSET
        if not isinstance(self.end_date, Unset):
            end_date = self.end_date.isoformat()

        status_filter: Unset | list[str] = UNSET
        if not isinstance(self.status_filter, Unset):
            status_filter = []
            for status_filter_item_data in self.status_filter:
                status_filter_item = status_filter_item_data.value
                status_filter.append(status_filter_item)

        format_: Unset | str = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if webhook_id is not UNSET:
            field_dict["webhook_id"] = webhook_id
        if start_date is not UNSET:
            field_dict["start_date"] = start_date
        if end_date is not UNSET:
            field_dict["end_date"] = end_date
        if status_filter is not UNSET:
            field_dict["status_filter"] = status_filter
        if format_ is not UNSET:
            field_dict["format"] = format_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        webhook_id = d.pop("webhook_id", UNSET)

        _start_date = d.pop("start_date", UNSET)
        start_date: Unset | datetime.datetime
        if isinstance(_start_date, Unset):
            start_date = UNSET
        else:
            start_date = isoparse(_start_date)

        _end_date = d.pop("end_date", UNSET)
        end_date: Unset | datetime.datetime
        if isinstance(_end_date, Unset):
            end_date = UNSET
        else:
            end_date = isoparse(_end_date)

        status_filter = []
        _status_filter = d.pop("status_filter", UNSET)
        for status_filter_item_data in _status_filter or []:
            status_filter_item = WebhookLogsExportRequestStatusFilterItem(
                status_filter_item_data
            )

            status_filter.append(status_filter_item)

        _format_ = d.pop("format", UNSET)
        format_: Unset | WebhookLogsExportRequestFormat
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = WebhookLogsExportRequestFormat(_format_)

        webhook_logs_export_request = cls(
            webhook_id=webhook_id,
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter,
            format_=format_,
        )

        return webhook_logs_export_request
