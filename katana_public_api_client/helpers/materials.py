"""Material catalog operations."""

from __future__ import annotations

from typing import Any, cast

from katana_public_api_client.api.material import (
    create_material,
    delete_material,
    get_all_materials,
    get_material,
    update_material,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.create_material_request import (
    CreateMaterialRequest,
)
from katana_public_api_client.models.material import Material
from katana_public_api_client.models.update_material_request import (
    UpdateMaterialRequest,
)
from katana_public_api_client.utils import unwrap, unwrap_data


class Materials(Base):
    """Material catalog management.

    Provides CRUD operations for materials in the Katana catalog.

    Example:
        >>> async with KatanaClient() as client:
        ...     # CRUD operations
        ...     materials = await client.materials.list()
        ...     material = await client.materials.get(123)
        ...     new_material = await client.materials.create({"name": "Steel"})
    """

    async def list(self, **filters: Any) -> list[Material]:
        """List all materials with optional filters.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of Material objects.

        Example:
            >>> materials = await client.materials.list(limit=100)
        """
        response = await get_all_materials.asyncio_detailed(
            client=self._client,
            **filters,
        )
        return unwrap_data(response)

    async def get(self, material_id: int) -> Material:
        """Get a specific material by ID.

        Args:
            material_id: The material ID.

        Returns:
            Material object.

        Example:
            >>> material = await client.materials.get(123)
        """
        response = await get_material.asyncio_detailed(
            client=self._client,
            id=material_id,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Material, unwrap(response))

    async def create(
        self, material_data: dict[str, Any] | CreateMaterialRequest
    ) -> Material:
        """Create a new material.

        Args:
            material_data: Material data dictionary or CreateMaterialRequest model.

        Returns:
            Created Material object.

        Example:
            >>> new_material = await client.materials.create({"name": "Steel"})
        """
        # Convert dict to model if needed
        if isinstance(material_data, dict):
            body = CreateMaterialRequest.from_dict(material_data)
        else:
            body = material_data

        response = await create_material.asyncio_detailed(
            client=self._client,
            body=body,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Material, unwrap(response))

    async def update(
        self, material_id: int, material_data: dict[str, Any] | UpdateMaterialRequest
    ) -> Material:
        """Update an existing material.

        Args:
            material_id: The material ID to update.
            material_data: Material data dictionary or UpdateMaterialRequest model with fields to update.

        Returns:
            Updated Material object.

        Example:
            >>> updated = await client.materials.update(123, {"name": "Aluminum"})
        """
        # Convert dict to model if needed
        if isinstance(material_data, dict):
            body = UpdateMaterialRequest.from_dict(material_data)
        else:
            body = material_data

        response = await update_material.asyncio_detailed(
            client=self._client,
            id=material_id,
            body=body,
        )
        # unwrap() raises on errors, so cast is safe
        return cast(Material, unwrap(response))

    async def delete(self, material_id: int) -> None:
        """Delete a material.

        Args:
            material_id: The material ID to delete.

        Example:
            >>> await client.materials.delete(123)
        """
        await delete_material.asyncio_detailed(
            client=self._client,
            id=material_id,
        )
