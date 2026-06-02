"""Live MCP-server smoke tests (issue #837, Phase 4).

These exercise a handful of high-traffic read-only MCP tool implementations
end-to-end against a real Katana **test tenant** — through the same
``Services`` (client + typed cache) path the server uses at runtime, not a
mock. They build on the Phase 1 ``make_test_client()`` helper and skip
automatically when ``KATANA_TEST_API_KEY`` is unset.

Marked ``smoke`` (run via ``poe test-smoke-mcp`` and the ``mcp-smoke`` job in
``live-integration.yml``) to keep them isolated from both the default suite
and the client-side ``live`` suite.
"""
