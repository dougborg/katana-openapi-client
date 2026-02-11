"""Logger protocol for duck-typed logger compatibility.

Defines a minimal Protocol that both ``logging.Logger`` and structlog's
``BoundLogger`` satisfy, so consumers can pass their already-configured
logger directly without adapters.

The public ``Logger`` type alias is a Union of ``logging.Logger`` (for nominal
compatibility with the ``ty`` type checker) and ``_LoggerProtocol`` (for
structural compatibility with duck-typed loggers like structlog).
"""

import logging
from typing import Any, Protocol


class _LoggerProtocol(Protocol):
    """Structural type for any object that exposes the four log methods the client uses."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


Logger = logging.Logger | _LoggerProtocol
"""Type alias accepted everywhere the client takes a logger parameter.

Both ``logging.Logger`` and any duck-typed logger (e.g. structlog's
``BoundLogger``) satisfying :class:`_LoggerProtocol` are accepted.
"""
