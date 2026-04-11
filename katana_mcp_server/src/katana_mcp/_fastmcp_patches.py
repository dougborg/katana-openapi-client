"""Patches for FastMCP compatibility issues.

This module patches FastMCP's get_cached_typeadapter to work correctly with
Pydantic 2.12+ and functions that use custom signatures.

The issue: FastMCP's get_cached_typeadapter creates new function objects with
updated __annotations__ but preserves the original __signature__. When Pydantic's
TypeAdapter iterates over signature parameters and looks them up in type_hints
(derived from __annotations__), it fails with KeyError for parameters that were
removed from __annotations__ but still exist in __signature__.

This patch updates __signature__ to match __annotations__ when creating
new function objects.

Note: The create_function_without_params fix was merged upstream in FastMCP 2.14+,
so only the get_cached_typeadapter patch is needed now.
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import Field, TypeAdapter

# Track whether patches have been applied (mutable container avoids global statement)
_state: dict[str, bool] = {"patched": False}


def _pin_annotate(target: Any, annotations: dict[str, Any]) -> None:
    """Override __annotate__ to return a frozen copy of the given annotations.

    Python 3.14+ (PEP 749) added __annotate__ which Pydantic prefers over
    __annotations__. When functools.wraps or __dict__.update() copies the
    original function's __annotate__, it returns stale annotations that don't
    match the modified __annotations__/__signature__, causing KeyError.

    This helper overrides __annotate__ with a lambda returning the correct
    annotations. For bound methods, patches __func__ since methods don't
    allow direct attribute assignment.
    """
    if inspect.ismethod(target):
        target = target.__func__
    if hasattr(target, "__annotate__"):
        frozen = dict(annotations)
        target.__annotate__ = lambda fmt: frozen


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
    sig = inspect.signature(fn)

    new_params = [
        p
        for param_name, p in sig.parameters.items()
        if param_name in new_annotations or param_name in ("args", "kwargs")
    ]
    # __signature__ is a valid but dynamic attribute on functions; assigning
    # it overrides inspect.signature()'s fallback to code-object introspection.
    # Use __dict__ to avoid static-typing friction around the dynamic attribute.
    fn.__dict__["__signature__"] = sig.replace(parameters=new_params)


@lru_cache(maxsize=5000)
def _patched_get_cached_typeadapter[T](cls: T) -> TypeAdapter[T]:
    """Patched version of FastMCP's get_cached_typeadapter.

    This version also updates __signature__ when creating new function objects,
    ensuring consistency with the updated __annotations__.
    """
    if (
        (inspect.isfunction(cls) or inspect.ismethod(cls))
        and hasattr(cls, "__annotations__")
        and cls.__annotations__
    ):
        try:
            resolved_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            resolved_hints = cls.__annotations__

        # Process annotations to convert string descriptions to Fields
        processed_hints = {}

        for name, annotation in resolved_hints.items():
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

            _pin_annotate(new_func, processed_hints)

            # PATCH: Also update __signature__ to match annotations
            _update_signature_to_match_annotations(new_func, processed_hints)

            if inspect.ismethod(cls):
                new_method = types.MethodType(new_func, cls.__self__)
                return TypeAdapter(new_method)
            else:
                return TypeAdapter(new_func)

    if (inspect.isfunction(cls) or inspect.ismethod(cls)) and hasattr(
        cls, "__annotations__"
    ):
        _pin_annotate(cls, cls.__annotations__)

    return TypeAdapter(cls)


def apply_fastmcp_patches() -> None:
    """Apply patches to FastMCP for Pydantic 2.12+ compatibility.

    This function should be called before any FastMCP tools are registered.
    It patches get_cached_typeadapter to update __signature__ when creating
    new function objects with modified annotations.
    """
    import fastmcp.tools.function_parsing
    import fastmcp.tools.function_tool
    import fastmcp.tools.tool_transform
    import fastmcp.utilities.types

    if _state["patched"]:
        return

    # Each fastmcp submodule imports get_cached_typeadapter by name at module
    # load time, so patching the source alone is not enough — we have to rebind
    # the local references in every submodule that imports it. Assign via
    # __dict__ so pyright doesn't flag the dynamic attribute write.
    patch = _patched_get_cached_typeadapter
    fastmcp.utilities.types.__dict__["get_cached_typeadapter"] = patch
    fastmcp.tools.function_parsing.__dict__["get_cached_typeadapter"] = patch
    fastmcp.tools.function_tool.__dict__["get_cached_typeadapter"] = patch
    fastmcp.tools.tool_transform.__dict__["get_cached_typeadapter"] = patch

    _state["patched"] = True
