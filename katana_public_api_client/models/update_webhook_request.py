from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.webhook_event import WebhookEvent

T = TypeVar("T", bound="UpdateWebhookRequest")


@_attrs_define
class UpdateWebhookRequest:
    """Request payload for updating an existing webhook subscription configuration

    Example:
        {'url': 'https://api.customer.com/webhooks/katana-v2', 'enabled': True, 'subscribed_events':
            ['sales_order.created', 'sales_order.updated', 'sales_order.delivered', 'current_inventory.product_updated',
            'manufacturing_order.done', 'purchase_order.received'], 'description': 'Updated ERP integration webhook with
            expanded event coverage'}
    """

    url: str | Unset = UNSET
    enabled: bool | Unset = UNSET
    subscribed_events: list[WebhookEvent] | Unset = UNSET
    description: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        enabled = self.enabled

        subscribed_events: list[str] | Unset = UNSET
        if not isinstance(self.subscribed_events, Unset):
            subscribed_events = []
            for subscribed_events_item_data in self.subscribed_events:
                subscribed_events_item = subscribed_events_item_data.value
                subscribed_events.append(subscribed_events_item)

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if url is not UNSET:
            field_dict["url"] = url
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if subscribed_events is not UNSET:
            field_dict["subscribed_events"] = subscribed_events
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url", UNSET)

        enabled = d.pop("enabled", UNSET)

        _subscribed_events = d.pop("subscribed_events", UNSET)
        subscribed_events: list[WebhookEvent] | Unset = UNSET
        if _subscribed_events is not UNSET:
            subscribed_events = []
            for subscribed_events_item_data in _subscribed_events:
                subscribed_events_item = WebhookEvent(subscribed_events_item_data)

                subscribed_events.append(subscribed_events_item)

        description = d.pop("description", UNSET)

        update_webhook_request = cls(
            url=url,
            enabled=enabled,
            subscribed_events=subscribed_events,
            description=description,
        )

        return update_webhook_request
