// Bundle the real MCP Apps host bridge and MCP client into one same-origin
// browser module. Exact versions live in package.json/package-lock.json.
export {
  AppBridge,
  PostMessageTransport,
  getToolUiResourceUri,
} from "@modelcontextprotocol/ext-apps/app-bridge";
export { Client } from "@modelcontextprotocol/sdk/client/index.js";
export { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
