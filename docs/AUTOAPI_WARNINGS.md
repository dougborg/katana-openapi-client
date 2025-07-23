# AutoAPI Duplicate Warnings Information

## Overview

When building documentation for this project, you may see warnings like:

```
WARNING: duplicate object description of katana_public_api_client.client.AuthenticatedClient.auth_header_name, other instance in autoapi/katana_public_api_client/client/index, use :no-index: for one of them
```

## Why This Happens

This is a **known issue** with Sphinx AutoAPI 3.2+ that occurs when:

1. Class attributes are documented in the class docstring (traditional Python style)
2. AutoAPI also generates typed `py:attribute` directives for the same attributes

This results in duplicate documentation entries that Sphinx detects and warns about.

## Impact

**These warnings are COSMETIC and do not affect documentation quality or functionality.**

- The generated documentation is complete and correct
- All API information is properly documented
- The warnings can be safely ignored

## Solutions

### For Local Development

The warnings will appear but can be ignored. The documentation builds successfully and is fully functional.

### For CI/CD Systems

If you need to suppress these warnings in automated builds, you can filter them:

```bash
# Filter out duplicate object warnings
sphinx-build -b html docs docs/_build/html 2>&1 | grep -v "duplicate object description"

# Or use the docs build command with filtering
poetry run poe docs-build 2>&1 | grep -v "duplicate object description"
```

### Configuration Changes Made

This project has already implemented several measures to minimize these warnings:

1. **AutoAPI Configuration**: Changed `autoapi_python_class_content` from "both" to "init" to reduce duplication
2. **Warning Suppression**: Added comprehensive `suppress_warnings` configuration
3. **Logging Levels**: Reduced verbosity for docutils and sphinx components
4. **Informative Messages**: Added explanations about the AutoAPI behavior

## Alternative Solutions

If these warnings are problematic for your use case, you can:

1. **Modify Docstrings**: Move attribute documentation from class docstrings to individual attribute docstrings directly after assignment in `__init__`
2. **Downgrade AutoAPI**: Use AutoAPI 3.1.x instead of 3.2+ (not recommended as you lose newer features)
3. **Custom Templates**: Create custom AutoAPI templates that handle attribute documentation differently

## References

- [Sphinx AutoAPI Issue #476](https://github.com/readthedocs/sphinx-autoapi/issues/476)
- [AutoAPI Changelog for 3.2.0](https://sphinx-autoapi.readthedocs.io/en/latest/changelog.html)

## Conclusion

The duplicate object warnings are a known cosmetic issue with AutoAPI 3.2+ that **do not affect the quality or completeness of the generated documentation**. The warnings can be safely ignored or filtered out in CI/CD systems as needed.