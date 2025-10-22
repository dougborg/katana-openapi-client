"""Base class for domain classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from katana_public_api_client.katana_client import KatanaClient


class Base:
    """Base class for all domain classes.

    Provides common functionality and access to the KatanaClient instance.

    Args:
        client: The KatanaClient instance to use for API calls.
    """

    def __init__(self, client: KatanaClient) -> None:
        """Initialize with a client instance.

        Args:
            client: The KatanaClient instance to use for API calls.
        """
        self._client = client
