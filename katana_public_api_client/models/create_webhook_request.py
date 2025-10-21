from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.webhook_event import WebhookEvent

T = TypeVar("T", bound="CreateWebhookRequest")


@_attrs_define
class CreateWebhookRequest:
    """Request payload for creating a new webhook subscription to receive real-time event notifications

    Example:
        {'url': 'https://api.customer.com/webhooks/katana', 'subscribed_events': ['sales_order.created',
            'sales_order.delivered', 'current_inventory.product_out_of_stock', 'manufacturing_order.done'], 'description':
            'ERP integration webhook for inventory and order sync'}

    Attributes:
        url (str): HTTPS endpoint URL where webhook events will be sent (must use HTTPS for security)
        subscribed_events (list[WebhookEvent]): List of event types to subscribe to (at least one event type required)
        description (Union[Unset, str]): Optional human-readable description of this webhook's purpose for management
            and documentation
    """

    url: str
    subscribed_events: list[WebhookEvent]
    description: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        subscribed_events = []
        for subscribed_events_item_data in self.subscribed_events:
            subscribed_events_item = subscribed_events_item_data.value
            subscribed_events.append(subscribed_events_item)

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "url": url,
                "subscribed_events": subscribed_events,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        subscribed_events = []
        _subscribed_events = d.pop("subscribed_events")
        for subscribed_events_item_data in _subscribed_events:
            subscribed_events_item = WebhookEvent(subscribed_events_item_data)

            subscribed_events.append(subscribed_events_item)

        description = d.pop("description", UNSET)

        create_webhook_request = cls(
            url=url,
            subscribed_events=subscribed_events,
            description=description,
        )

        return create_webhook_request
