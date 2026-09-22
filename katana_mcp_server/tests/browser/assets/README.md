# Browser bridge asset

`bridge.bundle.js` contains the real MCP Apps `AppBridge`, MCP client, and streamable
HTTP transport used by the browser render suite. Keeping this bundle in the repository
makes every browser page use the same pinned, same-origin modules instead of fetching
JavaScript from npm or esm.sh during a test run.

The exact source versions are locked in `package-lock.json`. Rebuild the bundle after
deliberately changing them:

```console
npm ci
npm run build
```

Commit the source, lockfile, and generated bundle together. The test launcher also
checks FastMCP's expected ext-apps and MCP SDK versions and fails at startup when either
contract changes.
