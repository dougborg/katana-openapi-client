"""Tests for the thin API wrapper layer (client.api)."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from katana_public_api_client.api_wrapper import (
    RESOURCE_REGISTRY,
    ApiNamespace,
    Resource,
    ResourceConfig,
)
from katana_public_api_client.utils import APIError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> MagicMock:
    """A minimal stand-in for AuthenticatedClient."""
    return MagicMock()


@pytest.fixture
def full_config() -> ResourceConfig:
    """A ResourceConfig with all five operations configured."""
    return ResourceConfig(
        module="product",
        get_one="get_product",
        get_all="get_all_products",
        create="create_product",
        update="update_product",
        delete="delete_product",
    )


@pytest.fixture
def readonly_config() -> ResourceConfig:
    """A ResourceConfig with only a list operation."""
    return ResourceConfig(
        module="operator",
        get_all="get_all_operators",
    )


# ---------------------------------------------------------------------------
# Resource CRUD dispatch
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResourceCrudDispatch:
    """Verify that each CRUD method calls the correct generated module."""

    async def test_get_calls_asyncio_detailed_with_id(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        sentinel = object()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                return_value=sentinel,
            ) as mock_unwrap,
        ):
            result = await resource.get(42, extend=["rows"])

        mock_mod.asyncio_detailed.assert_awaited_once_with(
            42, client=mock_client, extend=["rows"]
        )
        mock_unwrap.assert_called_once_with(mock_mod.asyncio_detailed.return_value)
        assert result is sentinel

    async def test_list_calls_asyncio_detailed_without_id(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        sentinel = [object()]
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap_data",
                return_value=sentinel,
            ) as mock_unwrap_data,
        ):
            result = await resource.list(limit=100)

        mock_mod.asyncio_detailed.assert_awaited_once_with(
            client=mock_client, limit=100
        )
        mock_unwrap_data.assert_called_once_with(
            mock_mod.asyncio_detailed.return_value, default=[]
        )
        assert result is sentinel

    async def test_create_passes_body(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        body = {"name": "Widget"}
        sentinel = object()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                return_value=sentinel,
            ),
        ):
            result = await resource.create(body)

        mock_mod.asyncio_detailed.assert_awaited_once_with(
            client=mock_client, body=body
        )
        assert result is sentinel

    async def test_update_passes_id_and_body(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        body = {"name": "Updated"}
        sentinel = object()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                return_value=sentinel,
            ),
        ):
            result = await resource.update(42, body)

        mock_mod.asyncio_detailed.assert_awaited_once_with(
            42, client=mock_client, body=body
        )
        assert result is sentinel

    async def test_delete_succeeds_on_204(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        # Simulate a 204 response: parsed=None, status_code=204
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.parsed = None
        mock_mod.asyncio_detailed = AsyncMock(return_value=mock_response)

        with patch.object(resource, "_load_module", return_value=mock_mod):
            result = await resource.delete(42)

        mock_mod.asyncio_detailed.assert_awaited_once_with(42, client=mock_client)
        assert result is None

    async def test_delete_raises_on_error(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        # Simulate a 404 error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_mod.asyncio_detailed = AsyncMock(return_value=mock_response)

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                side_effect=APIError(message="Not found", status_code=404),
            ),
            pytest.raises(APIError),
        ):
            await resource.delete(999)


# ---------------------------------------------------------------------------
# NotImplementedError for unconfigured operations
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResourceNotImplemented:
    """Verify clear errors for unconfigured CRUD operations."""

    async def test_get_raises_when_not_configured(
        self, mock_client: MagicMock, readonly_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, readonly_config)
        with pytest.raises(NotImplementedError, match="does not support the 'get'"):
            await resource.get(1)

    async def test_create_raises_when_not_configured(
        self, mock_client: MagicMock, readonly_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, readonly_config)
        with pytest.raises(NotImplementedError, match="does not support the 'create'"):
            await resource.create({"name": "x"})

    async def test_update_raises_when_not_configured(
        self, mock_client: MagicMock, readonly_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, readonly_config)
        with pytest.raises(NotImplementedError, match="does not support the 'update'"):
            await resource.update(1, {"name": "x"})

    async def test_delete_raises_when_not_configured(
        self, mock_client: MagicMock, readonly_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, readonly_config)
        with pytest.raises(NotImplementedError, match="does not support the 'delete'"):
            await resource.delete(1)


# ---------------------------------------------------------------------------
# ApiNamespace access & caching
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestApiNamespace:
    """Verify namespace lookup, caching, and error behaviour."""

    def test_returns_resource_for_valid_name(self, mock_client: MagicMock) -> None:
        ns = ApiNamespace(mock_client)
        resource = ns.products
        assert isinstance(resource, Resource)

    def test_caches_resource_across_accesses(self, mock_client: MagicMock) -> None:
        ns = ApiNamespace(mock_client)
        first = ns.products
        second = ns.products
        assert first is second

    def test_raises_attribute_error_for_unknown(self, mock_client: MagicMock) -> None:
        ns = ApiNamespace(mock_client)
        with pytest.raises(AttributeError, match="No resource named 'nonexistent'"):
            ns.nonexistent  # noqa: B018 (intentional attribute access)

    def test_error_message_lists_available_resources(
        self, mock_client: MagicMock
    ) -> None:
        ns = ApiNamespace(mock_client)
        with pytest.raises(AttributeError, match="Available resources:"):
            ns.nonexistent  # noqa: B018

    def test_dir_returns_registry_keys(self, mock_client: MagicMock) -> None:
        ns = ApiNamespace(mock_client)
        entries = dir(ns)
        assert entries == sorted(RESOURCE_REGISTRY)


# ---------------------------------------------------------------------------
# Registry completeness - every entry must point to importable modules
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRegistryCompleteness:
    """Ensure every registry entry references real generated API modules."""

    @pytest.mark.parametrize(
        "resource_name,config",
        list(RESOURCE_REGISTRY.items()),
        ids=list(RESOURCE_REGISTRY),
    )
    def test_all_configured_modules_are_importable(
        self, resource_name: str, config: ResourceConfig
    ) -> None:
        for op_name in ("get_one", "get_all", "create", "update", "delete"):
            func_name = getattr(config, op_name)
            if func_name is None:
                continue
            module_path = f"katana_public_api_client.api.{config.module}.{func_name}"
            try:
                mod = importlib.import_module(module_path)
            except ModuleNotFoundError:
                pytest.fail(
                    f"Registry entry '{resource_name}' references "
                    f"non-existent module: {module_path}"
                )
            assert hasattr(mod, "asyncio_detailed"), (
                f"{module_path} missing asyncio_detailed"
            )


# ---------------------------------------------------------------------------
# Kwargs passthrough
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestKwargsPassthrough:
    """Verify that extra kwargs (extend, filters, etc.) reach the module."""

    async def test_get_forwards_extend(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                return_value=None,
            ),
        ):
            await resource.get(1, extend=["rows", "ingredients"])

        _, kwargs = mock_mod.asyncio_detailed.call_args
        assert kwargs["extend"] == ["rows", "ingredients"]

    async def test_list_forwards_filters(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap_data",
                return_value=[],
            ),
        ):
            await resource.list(is_sellable=True, limit=50, include_archived=True)

        _, kwargs = mock_mod.asyncio_detailed.call_args
        assert kwargs["is_sellable"] is True
        assert kwargs["limit"] == 50
        assert kwargs["include_archived"] is True

    async def test_create_forwards_extra_kwargs(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())
        body = {"name": "Widget"}

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                return_value=None,
            ),
        ):
            await resource.create(body, extend=["rows"])

        _, kwargs = mock_mod.asyncio_detailed.call_args
        assert kwargs["body"] is body
        assert kwargs["extend"] == ["rows"]


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestErrorPropagation:
    """Verify that unwrap() exceptions bubble up transparently."""

    async def test_api_error_propagates_from_get(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap",
                side_effect=APIError(message="Not found", status_code=404),
            ),
            pytest.raises(APIError),
        ):
            await resource.get(999)

    async def test_api_error_propagates_from_list(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mock_mod = MagicMock()
        mock_mod.asyncio_detailed = AsyncMock(return_value=MagicMock())

        with (
            patch.object(resource, "_load_module", return_value=mock_mod),
            patch(
                "katana_public_api_client.api_wrapper._resource.unwrap_data",
                side_effect=APIError(message="Server error", status_code=500),
            ),
            pytest.raises(APIError),
        ):
            await resource.list()


# ---------------------------------------------------------------------------
# Lazy module loading & caching
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModuleLoading:
    """Verify lazy import and caching behaviour of Resource._load_module."""

    def test_load_module_imports_correct_path(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        mod = resource._load_module("get_product")
        assert hasattr(mod, "asyncio_detailed")

    def test_load_module_caches_result(
        self, mock_client: MagicMock, full_config: ResourceConfig
    ) -> None:
        resource = Resource(mock_client, full_config)
        first = resource._load_module("get_product")
        second = resource._load_module("get_product")
        assert first is second

    def test_load_module_rejects_unconfigured_func(
        self, mock_client: MagicMock
    ) -> None:
        config = ResourceConfig(module="nonexistent_api_dir")
        resource = Resource(mock_client, config)
        with pytest.raises(ValueError, match="not a configured operation"):
            resource._load_module("does_not_exist")


# ---------------------------------------------------------------------------
# KatanaClient.api integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestKatanaClientApiProperty:
    """Verify the .api property on KatanaClient."""

    def test_api_returns_namespace(self) -> None:
        with patch.dict("os.environ", {"KATANA_API_KEY": "test-key"}):
            from katana_public_api_client import KatanaClient

            client = KatanaClient(api_key="test-key")
            assert isinstance(client.api, ApiNamespace)

    def test_api_is_cached(self) -> None:
        with patch.dict("os.environ", {"KATANA_API_KEY": "test-key"}):
            from katana_public_api_client import KatanaClient

            client = KatanaClient(api_key="test-key")
            first = client.api
            second = client.api
            assert first is second
