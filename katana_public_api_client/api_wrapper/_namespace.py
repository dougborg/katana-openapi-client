"""Lazy namespace that exposes :class:`Resource` instances by name."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._registry import RESOURCE_REGISTRY
from ._resource import Resource

if TYPE_CHECKING:
    from ..client import AuthenticatedClient


class ApiNamespace:
    """Dynamic namespace providing ``client.api.<resource>`` access.

    Resources are created lazily on first attribute access and cached on the
    instance for subsequent calls.  Tab-completion is supported via
    :meth:`__dir__`.
    """

    def __init__(self, client: AuthenticatedClient) -> None:
        self._client = client

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            config = RESOURCE_REGISTRY[name]
        except KeyError:
            available = ", ".join(sorted(RESOURCE_REGISTRY))
            msg = f"No resource named '{name}'. Available resources: {available}"
            raise AttributeError(msg) from None
        resource = Resource(self._client, config)
        # Cache on the instance so __getattr__ is not called again
        object.__setattr__(self, name, resource)
        return resource

    def __dir__(self) -> list[str]:
        return sorted(RESOURCE_REGISTRY)
