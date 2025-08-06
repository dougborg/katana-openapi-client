"""API response object."""

from __future__ import annotations

from typing import Any

from pydantic import Field, StrictInt, StrictStr


class ApiResponse:
    """
    API response object
    """

    status_code: StrictInt | None = Field(None, description="HTTP status code")
    headers: dict[StrictStr, StrictStr] | None = Field(None, description="HTTP headers")
    data: Any | None = Field(None, description="Deserialized data given the data type")
    raw_data: Any | None = Field(None, description="Raw data (HTTP response body)")

    def __init__(
        self, status_code=None, headers=None, data=None, raw_data=None
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.data = data
        self.raw_data = raw_data
