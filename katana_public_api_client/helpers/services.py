"""Service catalog operations."""

from __future__ import annotations

from typing import Any, cast

from katana_public_api_client.api.services import (
    create_service,
    delete_service,
    get_all_services,
    get_service,
    update_service,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.create_service_request import CreateServiceRequest
from katana_public_api_client.models.service import Service
from katana_public_api_client.models.update_service_request import UpdateServiceRequest
from katana_public_api_client.utils import unwrap, unwrap_data


class Services(Base):
    """Service catalog management.

    Provides CRUD operations for services in the Katana catalog.

    Example:
        >>> async with KatanaClient() as client:
        ...     # CRUD operations
        ...     services = await client.services.list()
        ...     service = await client.services.get(123)
        ...     new_service = await client.services.create({"name": "Assembly"})
    """

    async def list(self, **filters: Any) -> list[Service]:
        """List all services with optional filters.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of Service objects.

        Example:
            >>> services = await client.services.list(limit=100)
        """
        response = await get_all_services.asyncio_detailed(
            client=self._client,
            **filters,
        )
        return unwrap_data(response)

    async def get(self, service_id: int) -> Service:
        """Get a specific service by ID.

        Args:
            service_id: The service ID.

        Returns:
            Service object.

        Example:
            >>> service = await client.services.get(123)
        """
        response = await get_service.asyncio_detailed(
            client=self._client,
            id=service_id,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Service, unwrap(response))

    async def create(self, service_data: CreateServiceRequest) -> Service:
        """Create a new service.

        Args:
            service_data: CreateServiceRequest model with service details.

        Returns:
            Created Service object.

        Example:
            >>> from katana_public_api_client.models import CreateServiceRequest
            >>> new_service = await client.services.create(
            ...     CreateServiceRequest(name="Assembly")
            ... )
        """
        response = await create_service.asyncio_detailed(
            client=self._client,
            body=service_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Service, unwrap(response))

    async def update(
        self, service_id: int, service_data: UpdateServiceRequest
    ) -> Service:
        """Update an existing service.

        Args:
            service_id: The service ID to update.
            service_data: UpdateServiceRequest model with fields to update.

        Returns:
            Updated Service object.

        Example:
            >>> from katana_public_api_client.models import UpdateServiceRequest
            >>> updated = await client.services.update(
            ...     123, UpdateServiceRequest(name="QA Testing")
            ... )
        """
        response = await update_service.asyncio_detailed(
            client=self._client,
            id=service_id,
            body=service_data,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Service, unwrap(response))

    async def delete(self, service_id: int) -> None:
        """Delete a service.

        Args:
            service_id: The service ID to delete.

        Example:
            >>> await client.services.delete(123)
        """
        await delete_service.asyncio_detailed(
            client=self._client,
            id=service_id,
        )
