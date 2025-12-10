"""Patches for FastMCP compatibility issues.

This module patches FastMCP's function handling to work correctly with
Pydantic 2.12+ and functions that use custom signatures.

The issue: FastMCP's create_function_without_params and get_cached_typeadapter
functions create new function objects with updated __annotations__ but preserve
the original __signature__. When Pydantic's TypeAdapter iterates over signature
parameters and looks them up in type_hints (derived from __annotations__), it
fails with KeyError for parameters that were removed from __annotations__ but
still exist in __signature__.

This patch updates __signature__ to match __annotations__ when creating
new function objects.

See: https://github.com/jlowin/fastmcp/issues/XXXX (to be filed)
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import Field, TypeAdapter

# Store original functions for reference (using dict to avoid global statement)
_originals: dict[str, Callable[..., Any] | None] = {
    "create_function_without_params": None,
    "get_cached_typeadapter": None,
}


def _update_signature_to_match_annotations(
    fn: Callable[..., Any], new_annotations: dict[str, Any]
) -> None:
    """Update a function's __signature__ to only include parameters in new_annotations.

    This ensures __signature__ is consistent with __annotations__, which is required
    for Pydantic's TypeAdapter to work correctly.

    IMPORTANT: We must always SET __signature__ because inspect.signature() falls back
    to introspecting the code object when __signature__ doesn't exist. By setting
    __signature__, we override that fallback behavior.
    """
    # Get current signature - this works whether __signature__ exists or not
    # If __signature__ doesn't exist, inspect.signature() introspects the code object
    sig = inspect.signature(fn)

    new_params = [
        p
        for param_name, p in sig.parameters.items()
        if param_name in new_annotations or param_name in ("args", "kwargs")
    ]
    fn.__signature__ = sig.replace(parameters=new_params)


def _patched_create_function_without_params(
    fn: Callable[..., Any], exclude_params: list[str]
) -> Callable[..., Any]:
    """Patched version of FastMCP's create_function_without_params.

    This version also updates __signature__ to remove the excluded parameters,
    ensuring consistency with the updated __annotations__.
    """
    if inspect.ismethod(fn):
        actual_func = fn.__func__
        code = actual_func.__code__
        globals_dict = actual_func.__globals__
        name = actual_func.__name__
        defaults = actual_func.__defaults__
        closure = actual_func.__closure__
    else:
        code = fn.__code__
        globals_dict = fn.__globals__
        name = fn.__name__
        defaults = fn.__defaults__
        closure = fn.__closure__

    # Create a copy of annotations without the excluded parameters
    original_annotations = getattr(fn, "__annotations__", {})
    new_annotations = {
        k: v for k, v in original_annotations.items() if k not in exclude_params
    }

    new_func = types.FunctionType(
        code,
        globals_dict,
        name,
        defaults,
        closure,
    )
    new_func.__dict__.update(fn.__dict__)
    new_func.__module__ = fn.__module__
    new_func.__qualname__ = getattr(fn, "__qualname__", fn.__name__)
    new_func.__annotations__ = new_annotations

    # PATCH: Also update __signature__ to remove excluded parameters
    _update_signature_to_match_annotations(new_func, new_annotations)

    if inspect.ismethod(fn):
        return types.MethodType(new_func, fn.__self__)
    else:
        return new_func


@lru_cache(maxsize=5000)
def _patched_get_cached_typeadapter[T](cls: T) -> TypeAdapter[T]:
    """Patched version of FastMCP's get_cached_typeadapter.

    This version also updates __signature__ when creating new function objects,
    ensuring consistency with the updated __annotations__.
    """
    # For functions, process annotations to handle forward references and convert
    # Annotated[Type, "string"] to Annotated[Type, Field(description="string")]
    if (
        (inspect.isfunction(cls) or inspect.ismethod(cls))
        and hasattr(cls, "__annotations__")
        and cls.__annotations__
    ):
        try:
            # Resolve forward references first
            resolved_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            # If forward reference resolution fails, use original annotations
            resolved_hints = cls.__annotations__

        # Process annotations to convert string descriptions to Fields
        processed_hints = {}

        for name, annotation in resolved_hints.items():
            # Check if this is Annotated[Type, "string"] and convert to Annotated[Type, Field(description="string")]
            if (
                get_origin(annotation) is Annotated
                and len(get_args(annotation)) == 2
                and isinstance(get_args(annotation)[1], str)
            ):
                base_type, description = get_args(annotation)
                processed_hints[name] = Annotated[
                    base_type, Field(description=description)
                ]
            else:
                processed_hints[name] = annotation

        # Create new function if annotations changed
        if processed_hints != cls.__annotations__:
            # Handle both functions and methods
            if inspect.ismethod(cls):
                actual_func = cls.__func__
                code = actual_func.__code__
                globals_dict = actual_func.__globals__
                name = actual_func.__name__
                defaults = actual_func.__defaults__
                closure = actual_func.__closure__
            else:
                code = cls.__code__
                globals_dict = cls.__globals__
                name = cls.__name__
                defaults = cls.__defaults__
                closure = cls.__closure__

            new_func = types.FunctionType(
                code,
                globals_dict,
                name,
                defaults,
                closure,
            )
            new_func.__dict__.update(cls.__dict__)
            new_func.__module__ = cls.__module__
            new_func.__qualname__ = getattr(cls, "__qualname__", cls.__name__)
            new_func.__annotations__ = processed_hints

            # PATCH: Also update __signature__ to match annotations
            _update_signature_to_match_annotations(new_func, processed_hints)

            if inspect.ismethod(cls):
                new_method = types.MethodType(new_func, cls.__self__)
                return TypeAdapter(new_method)
            else:
                return TypeAdapter(new_func)

    return TypeAdapter(cls)


def apply_fastmcp_patches() -> None:
    """Apply patches to FastMCP for Pydantic 2.12+ compatibility.

    This function should be called before any FastMCP tools are registered.
    It patches the following functions:
    - fastmcp.tools.tool.create_function_without_params
    - fastmcp.utilities.types.get_cached_typeadapter
    - fastmcp.tools.tool.get_cached_typeadapter (local reference)
    """
    import fastmcp.tools.tool
    import fastmcp.utilities.types

    # Only patch once
    if _originals["create_function_without_params"] is not None:
        return

    _originals["create_function_without_params"] = (
        fastmcp.tools.tool.create_function_without_params
    )
    fastmcp.tools.tool.create_function_without_params = (
        _patched_create_function_without_params
    )

    _originals["get_cached_typeadapter"] = (
        fastmcp.utilities.types.get_cached_typeadapter
    )
    fastmcp.utilities.types.get_cached_typeadapter = _patched_get_cached_typeadapter

    # Also patch the local reference in fastmcp.tools.tool
    # This is necessary because `from ...utilities.types import get_cached_typeadapter`
    # creates a local binding that isn't affected by patching the original module
    fastmcp.tools.tool.get_cached_typeadapter = _patched_get_cached_typeadapter


# Auto-apply patches when this module is imported
apply_fastmcp_patches()
