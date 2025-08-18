"""Tests for OpenAPI specification validation."""

from pathlib import Path

import yaml


class TestOpenAPIValidation:
    """Test OpenAPI specification validation."""

    def test_openapi_file_exists(self):
        """Test that the OpenAPI specification file exists."""
        openapi_file = Path("docs/katana-openapi.yaml")
        assert openapi_file.exists(), "OpenAPI specification file not found"

    def test_openapi_file_is_valid_yaml(self):
        """Test that the OpenAPI file is valid YAML."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        assert spec is not None, "OpenAPI file should contain valid YAML"
        assert isinstance(spec, dict), "OpenAPI spec should be a dictionary"

    def test_openapi_version(self):
        """Test that the OpenAPI specification uses version 3.1.x."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        assert "openapi" in spec, "OpenAPI specification must have 'openapi' field"
        version = spec["openapi"]
        assert version.startswith("3.1"), f"Expected OpenAPI 3.1.x, got {version}"

    def test_openapi_required_sections(self):
        """Test that the OpenAPI specification has all required sections."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        required_sections = ["openapi", "info", "paths"]
        for section in required_sections:
            assert section in spec, f"OpenAPI spec missing required section: {section}"

    def test_openapi_info_section(self):
        """Test that the info section has required fields."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        info = spec.get("info", {})
        assert "title" in info, "OpenAPI info section must have 'title'"
        assert "version" in info, "OpenAPI info section must have 'version'"

    def test_openapi_endpoints_exist(self):
        """Test that the OpenAPI specification defines endpoints."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        paths = spec.get("paths", {})
        assert len(paths) > 0, "OpenAPI spec should define at least one endpoint"

        # Should have a reasonable number of endpoints for Katana API
        assert len(paths) >= 50, f"Expected at least 50 endpoints, found {len(paths)}"

    def test_openapi_components_section(self):
        """Test that the OpenAPI specification has components section."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        # Components section is optional but should exist for a real API
        if "components" in spec:
            components = spec["components"]
            assert isinstance(components, dict), (
                "Components section should be a dictionary"
            )

            # Should have schemas for data models
            if "schemas" in components:
                schemas = components["schemas"]
                assert len(schemas) > 0, "Should have at least one schema defined"

    def test_openapi_security_definitions(self):
        """Test that the OpenAPI specification defines security schemes."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        # Check for security definitions
        has_security = "security" in spec or (
            "components" in spec and "securitySchemes" in spec.get("components", {})
        )

        assert has_security, "OpenAPI spec should define security schemes"

    def test_endpoint_methods(self):
        """Test that endpoints define proper HTTP methods."""
        openapi_file = Path("docs/katana-openapi.yaml")

        with open(openapi_file) as f:
            spec = yaml.safe_load(f)

        paths = spec.get("paths", {})
        valid_methods = {"get", "post", "put", "patch", "delete", "options", "head"}

        for path, path_spec in paths.items():
            assert isinstance(path_spec, dict), f"Path spec for {path} should be a dict"

            for method in path_spec:
                if method not in ["parameters", "summary", "description"]:
                    assert method.lower() in valid_methods, (
                        f"Invalid HTTP method: {method}"
                    )
