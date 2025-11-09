"""Unpack decorator for flattening Pydantic models into tool parameters.

This module provides a decorator that allows tools to use Pydantic models for
validation while exposing flattened parameters to the MCP protocol, working around
Claude Code's parameter serialization issues with nested objects.

Usage:
    from typing import Annotated
    from pydantic import BaseModel, Field
    from katana_mcp.unpack import Unpack, unpack_pydantic_params

    class MyRequest(BaseModel):
        name: str = Field(..., description="Item name")
        limit: int = Field(10, description="Max results")

    @unpack_pydantic_params
    async def my_tool(
        request: Annotated[MyRequest, Unpack()],
        context: Context
    ) -> MyResponse:
        # request is a MyRequest instance with validated fields
        ...

The decorator transforms the function signature so FastMCP sees individual
parameters (name, limit) instead of a nested request object, while the function
body still receives a properly validated Pydantic model instance.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined


class Unpack:
    """Marker class to indicate a Pydantic model should be unpacked into flat parameters.

    Use with typing.Annotated to mark which parameters should be unpacked:
        request: Annotated[MyRequest, Unpack()]
    """

    pass


def unpack_pydantic_params(func: Callable) -> Callable:
    """Decorator that unpacks Pydantic model parameters into individual fields.

    This decorator scans the function signature for parameters annotated with
    Annotated[ModelClass, Unpack()], extracts the Pydantic model fields, and
    creates a new function that accepts those fields as individual parameters.

    At runtime, the individual parameters are collected and used to construct
    the Pydantic model instance, which is then passed to the original function.

    Args:
        func: The function to decorate. Should have at least one parameter
              annotated with Annotated[BaseModel, Unpack()].

    Returns:
        A wrapped function with flattened parameters that reconstructs the
        Pydantic model at runtime.

    Raises:
        TypeError: If the unpacked parameter is not a Pydantic BaseModel subclass.
        ValidationError: If the collected parameters don't pass Pydantic validation.

    Example:
        @unpack_pydantic_params
        async def search_items(
            request: Annotated[SearchRequest, Unpack()],
            context: Context
        ) -> SearchResponse:
            # request is a validated SearchRequest instance
            return await search_impl(request, context)

        # FastMCP sees: search_items(query: str, limit: int, context: Context)
        # Function receives: request=SearchRequest(query="...", limit=20)
    """
    sig = inspect.signature(func)
    new_params = []
    unpack_mapping: dict[str, tuple[type[BaseModel], list[str]]] = {}

    # Get type hints to resolve string annotations (from __future__ import annotations)
    try:
        type_hints = get_type_hints(func, include_extras=True)
    except Exception:
        # If get_type_hints() fails, fall back to raw annotations
        type_hints = {}

    # Track if we've added any KEYWORD_ONLY params
    # If we have, all subsequent params must also be KEYWORD_ONLY
    has_keyword_only = False

    # Scan parameters to find ones marked with Unpack()
    for param_name, param in sig.parameters.items():
        # Use resolved type hint if available, otherwise use raw annotation
        annotation = type_hints.get(param_name, param.annotation)

        # Check if this is Annotated[SomeModel, Unpack()]
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            if len(args) >= 2 and any(isinstance(arg, Unpack) for arg in args[1:]):
                # Found an unpacked parameter
                model_class = args[0]

                if not (
                    inspect.isclass(model_class) and issubclass(model_class, BaseModel)
                ):
                    raise TypeError(
                        f"Parameter '{param_name}' with Unpack() must be a Pydantic BaseModel, "
                        f"got {model_class}"
                    )

                # Extract fields from the Pydantic model
                # Store fields to add them in correct order later
                unpacked_fields = []
                for field_name, field_info in model_class.model_fields.items():
                    # Create parameter for each model field
                    field_annotation = field_info.annotation

                    # Handle default values - convert PydanticUndefined to inspect.Parameter.empty
                    if field_info.default is not PydanticUndefined:
                        field_default = field_info.default
                    elif field_info.default_factory:
                        field_default = field_info.default_factory()
                    else:
                        field_default = inspect.Parameter.empty

                    # Use KEYWORD_ONLY to avoid parameter ordering issues
                    # This allows unpacked params to work with other params like Context
                    new_param = inspect.Parameter(
                        name=field_name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        default=field_default,
                        annotation=field_annotation,
                    )
                    unpacked_fields.append(new_param)

                # Add all unpacked fields
                new_params.extend(unpacked_fields)
                has_keyword_only = True

                # Remember this mapping for runtime reconstruction
                unpack_mapping[param_name] = (
                    model_class,
                    list(model_class.model_fields.keys()),
                )
                continue

        # Keep non-unpacked parameters, but if we've added KEYWORD_ONLY params
        # before this, we need to make this KEYWORD_ONLY too
        if has_keyword_only and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            new_params.append(param.replace(kind=inspect.Parameter.KEYWORD_ONLY))
        else:
            new_params.append(param)

    # Create new signature with flattened parameters
    new_sig = sig.replace(parameters=new_params)

    # Create wrapper function that reconstructs models at runtime
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Reconstruct Pydantic models from flat parameters
        reconstructed_kwargs = kwargs.copy()

        for original_param_name, (model_class, field_names) in unpack_mapping.items():
            # Collect fields for this model
            model_data = {}
            for field_name in field_names:
                if field_name in kwargs:
                    model_data[field_name] = kwargs.pop(field_name)

            # Build and validate the model
            try:
                model_instance = model_class(**model_data)
            except ValidationError:
                # Re-raise Pydantic validation errors as-is
                raise

            # Add reconstructed model to kwargs
            reconstructed_kwargs = {
                k: v for k, v in reconstructed_kwargs.items() if k not in field_names
            }
            reconstructed_kwargs[original_param_name] = model_instance

        return await func(*args, **reconstructed_kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Reconstruct Pydantic models from flat parameters
        reconstructed_kwargs = kwargs.copy()

        for original_param_name, (model_class, field_names) in unpack_mapping.items():
            # Collect fields for this model
            model_data = {}
            for field_name in field_names:
                if field_name in kwargs:
                    model_data[field_name] = kwargs.pop(field_name)

            # Build and validate the model
            try:
                model_instance = model_class(**model_data)
            except ValidationError:
                # Re-raise Pydantic validation errors as-is
                raise

            # Add reconstructed model to kwargs
            reconstructed_kwargs = {
                k: v for k, v in reconstructed_kwargs.items() if k not in field_names
            }
            reconstructed_kwargs[original_param_name] = model_instance

        return func(*args, **reconstructed_kwargs)

    # Choose wrapper based on whether original function is async
    wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    # Update wrapper signature to show flattened parameters
    wrapper.__signature__ = new_sig  # type: ignore[attr-defined]

    # CRITICAL: Also update __annotations__ so get_type_hints() sees the flattened params
    # This is required for FastMCP's ParsedFunction.from_function() to work correctly
    new_annotations = {}
    for param_name, param in new_sig.parameters.items():
        if param.annotation != inspect.Parameter.empty:
            new_annotations[param_name] = param.annotation
    if new_sig.return_annotation != inspect.Signature.empty:
        new_annotations["return"] = new_sig.return_annotation
    wrapper.__annotations__ = new_annotations

    return wrapper


__all__ = ["Unpack", "unpack_pydantic_params"]
