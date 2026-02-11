"""Generic async CRUD resource that delegates to generated API modules."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from ..utils import is_success, unwrap, unwrap_data

if TYPE_CHECKING:
    from types import ModuleType

    from ..client import AuthenticatedClient
    from ._registry import ResourceConfig

_list = list  # alias to avoid shadowing by the method name


class Resource:
    """Thin async CRUD wrapper around a single Katana API resource.

    Each method delegates to the corresponding generated ``asyncio_detailed``
    function, unwraps the response, and returns the raw *attrs* model.

    Generated modules are imported lazily on first call and cached for reuse.
    """

    def __init__(self, client: AuthenticatedClient, config: ResourceConfig) -> None:
        self._client = client
        self._config = config
        self._module_cache: dict[str, ModuleType] = {}

    # -- helpers ---------------------------------------------------------------

    def _load_module(self, func_name: str) -> ModuleType:
        """Import and cache a generated API module by function name.

        Only values from the frozen :class:`ResourceConfig` are accepted;
        the import path is always
        ``katana_public_api_client.api.<module>.<func_name>``.
        """
        if func_name not in self._module_cache:
            # Validate that func_name is one of the config's known values
            # so the import path is guaranteed to be from the registry.
            allowed = {
                self._config.get_one,
                self._config.get_all,
                self._config.create,
                self._config.update,
                self._config.delete,
            }
            if func_name not in allowed:
                msg = f"'{func_name}' is not a configured operation for '{self._config.module}'"
                raise ValueError(msg)
            path = f"katana_public_api_client.api.{self._config.module}.{func_name}"
            self._module_cache[func_name] = importlib.import_module(path)
        return self._module_cache[func_name]

    def _require(self, operation: str, func_name: str | None) -> str:
        """Return *func_name* or raise ``NotImplementedError``."""
        if func_name is None:
            msg = (
                f"'{self._config.module}' does not support the '{operation}' operation"
            )
            raise NotImplementedError(msg)
        return func_name

    # -- CRUD ------------------------------------------------------------------

    async def get(self, resource_id: int, **kwargs: Any) -> Any:
        """Fetch a single resource by ID."""
        name = self._require("get", self._config.get_one)
        mod = self._load_module(name)
        response = await mod.asyncio_detailed(
            resource_id, client=self._client, **kwargs
        )
        return unwrap(response)

    async def list(self, **kwargs: Any) -> _list[Any]:
        """Fetch all resources (with optional filters)."""
        name = self._require("list", self._config.get_all)
        mod = self._load_module(name)
        response = await mod.asyncio_detailed(client=self._client, **kwargs)
        return unwrap_data(response, default=[])

    async def create(self, body: Any, **kwargs: Any) -> Any:
        """Create a new resource."""
        name = self._require("create", self._config.create)
        mod = self._load_module(name)
        response = await mod.asyncio_detailed(client=self._client, body=body, **kwargs)
        return unwrap(response)

    async def update(self, resource_id: int, body: Any, **kwargs: Any) -> Any:
        """Update an existing resource by ID."""
        name = self._require("update", self._config.update)
        mod = self._load_module(name)
        response = await mod.asyncio_detailed(
            resource_id, client=self._client, body=body, **kwargs
        )
        return unwrap(response)

    async def delete(self, resource_id: int, **kwargs: Any) -> None:
        """Delete a resource by ID.  Raises on error, returns ``None``."""
        name = self._require("delete", self._config.delete)
        mod = self._load_module(name)
        response = await mod.asyncio_detailed(
            resource_id, client=self._client, **kwargs
        )
        # DELETE endpoints return 204 with parsed=None on success;
        # unwrap() would raise on None, so check status first.
        if not is_success(response):
            unwrap(response)  # raises the appropriate typed error
