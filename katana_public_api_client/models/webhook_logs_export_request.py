from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.webhook_logs_export_request_event import WebhookLogsExportRequestEvent

T = TypeVar("T", bound="WebhookLogsExportRequest")


@_attrs_define
class WebhookLogsExportRequest:
    """Request parameters for exporting webhook delivery logs for analysis and debugging

    Example:
        {'webhook_id': 1, 'event': 'sales_order.created', 'status_code': 200, 'delivered': True, 'created_at_min':
            '2024-01-10T00:00:00Z', 'created_at_max': '2024-01-15T23:59:59Z'}
    """

    webhook_id: int | Unset = UNSET
    event: WebhookLogsExportRequestEvent | Unset = UNSET
    status_code: int | Unset = UNSET
    delivered: bool | Unset = UNSET
    created_at_min: str | Unset = UNSET
    created_at_max: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        webhook_id = self.webhook_id

        event: str | Unset = UNSET
        if not isinstance(self.event, Unset):
            event = self.event.value

        status_code = self.status_code

        delivered = self.delivered

        created_at_min = self.created_at_min

        created_at_max = self.created_at_max

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if webhook_id is not UNSET:
            field_dict["webhook_id"] = webhook_id
        if event is not UNSET:
            field_dict["event"] = event
        if status_code is not UNSET:
            field_dict["status_code"] = status_code
        if delivered is not UNSET:
            field_dict["delivered"] = delivered
        if created_at_min is not UNSET:
            field_dict["created_at_min"] = created_at_min
        if created_at_max is not UNSET:
            field_dict["created_at_max"] = created_at_max

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        webhook_id = d.pop("webhook_id", UNSET)

        _event = d.pop("event", UNSET)
        event: WebhookLogsExportRequestEvent | Unset
        if isinstance(_event, Unset):
            event = UNSET
        else:
            event = WebhookLogsExportRequestEvent(_event)

        status_code = d.pop("status_code", UNSET)

        delivered = d.pop("delivered", UNSET)

        created_at_min = d.pop("created_at_min", UNSET)

        created_at_max = d.pop("created_at_max", UNSET)

        webhook_logs_export_request = cls(
            webhook_id=webhook_id,
            event=event,
            status_code=status_code,
            delivered=delivered,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
        )

        return webhook_logs_export_request
