"""Material catalog operations."""

from typing import Any

from katana_public_api_client.api.material import (
    create_material,
    delete_material,
    get_all_materials,
    get_material,
    update_material,
)
from katana_public_api_client.helpers.base import Base
from katana_public_api_client.models.material import Material
from katana_public_api_client.utils import unwrap_data


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
        return unwrap_data(response)

    async def create(self, material_data: dict[str, Any]) -> Material:
        """Create a new material.

        Args:
            material_data: Material data dictionary.

        Returns:
            Created Material object.

        Example:
            >>> new_material = await client.materials.create({"name": "Steel"})
        """
        response = await create_material.asyncio_detailed(
            client=self._client,
            body=material_data,
        )
        return unwrap_data(response)

    async def update(self, material_id: int, material_data: dict[str, Any]) -> Material:
        """Update an existing material.

        Args:
            material_id: The material ID to update.
            material_data: Material data dictionary with fields to update.

        Returns:
            Updated Material object.

        Example:
            >>> updated = await client.materials.update(123, {"name": "Aluminum"})
        """
        response = await update_material.asyncio_detailed(
            client=self._client,
            id=material_id,
            body=material_data,
        )
        return unwrap_data(response)

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
