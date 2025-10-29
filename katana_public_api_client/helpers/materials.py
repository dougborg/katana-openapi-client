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
from katana_public_api_client.domain import (
    KatanaMaterial,
    material_to_katana,
    materials_to_katana,
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

    async def list(self, **filters: Any) -> list[KatanaMaterial]:
        """List all materials with optional filters.

        Args:
            **filters: Filtering parameters.

        Returns:
            List of KatanaMaterial domain model objects.

        Example:
            >>> materials = await client.materials.list(limit=100)
        """
        response = await get_all_materials.asyncio_detailed(
            client=self._client,
            **filters,
        )
        attrs_materials = unwrap_data(response)
        return materials_to_katana(attrs_materials)

    async def get(self, material_id: int) -> KatanaMaterial:
        """Get a specific material by ID.

        Args:
            material_id: The material ID.

        Returns:
            KatanaMaterial domain model object.

        Example:
            >>> material = await client.materials.get(123)
        """
        response = await get_material.asyncio_detailed(
            client=self._client,
            id=material_id,
        )
        # unwrap() raises on errors, so cast is safe
        attrs_material = cast(Material, unwrap(response))
        return material_to_katana(attrs_material)

    async def create(self, material_data: CreateMaterialRequest) -> KatanaMaterial:
        """Create a new material.

        Args:
            material_data: CreateMaterialRequest model with material details.

        Returns:
            Created KatanaMaterial domain model object.

        Example:
            >>> from katana_public_api_client.models import CreateMaterialRequest
            >>> new_material = await client.materials.create(
            ...     CreateMaterialRequest(name="Steel")
            ... )
        """
        response = await create_material.asyncio_detailed(
            client=self._client,
            body=material_data,
        )
        # unwrap() raises on errors, so cast is safe
        attrs_material = cast(Material, unwrap(response))
        return material_to_katana(attrs_material)

    async def update(
        self, material_id: int, material_data: UpdateMaterialRequest
    ) -> KatanaMaterial:
        """Update an existing material.

        Args:
            material_id: The material ID to update.
            material_data: UpdateMaterialRequest model with fields to update.

        Returns:
            Updated KatanaMaterial domain model object.

        Example:
            >>> from katana_public_api_client.models import UpdateMaterialRequest
            >>> updated = await client.materials.update(
            ...     123, UpdateMaterialRequest(name="Aluminum")
            ... )
        """
        response = await update_material.asyncio_detailed(
            client=self._client,
            id=material_id,
            body=material_data,
        )
        # unwrap() raises on errors, so cast is safe
        attrs_material = cast(Material, unwrap(response))
        return material_to_katana(attrs_material)

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
