import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookResponse")


@_attrs_define
class WebhookResponse:
    """
    Attributes:
        id (Union[Unset, int]):
        url (Union[Unset, str]):
        token (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        description (Union[None, Unset, str]):
        subscribed_events (Union[Unset, list[str]]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    id: Unset | int = UNSET
    url: Unset | str = UNSET
    token: Unset | str = UNSET
    enabled: Unset | bool = UNSET
    description: None | Unset | str = UNSET
    subscribed_events: Unset | list[str] = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        url = self.url

        token = self.token

        enabled = self.enabled

        description: None | Unset | str
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        subscribed_events: Unset | list[str] = UNSET
        if not isinstance(self.subscribed_events, Unset):
            subscribed_events = self.subscribed_events

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if url is not UNSET:
            field_dict["url"] = url
        if token is not UNSET:
            field_dict["token"] = token
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if description is not UNSET:
            field_dict["description"] = description
        if subscribed_events is not UNSET:
            field_dict["subscribed_events"] = subscribed_events
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        url = d.pop("url", UNSET)

        token = d.pop("token", UNSET)

        enabled = d.pop("enabled", UNSET)

        def _parse_description(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        description = _parse_description(d.pop("description", UNSET))

        subscribed_events = cast(list[str], d.pop("subscribed_events", UNSET))

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

        webhook_response = cls(
            id=id,
            url=url,
            token=token,
            enabled=enabled,
            description=description,
            subscribed_events=subscribed_events,
            created_at=created_at,
            updated_at=updated_at,
        )

        webhook_response.additional_properties = d
        return webhook_response

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
