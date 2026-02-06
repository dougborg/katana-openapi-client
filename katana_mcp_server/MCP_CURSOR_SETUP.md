# Katana MCP Server - Cursor IDE Setup

This guide explains how to run the Katana MCP server independently and connect Cursor
IDE to it via SSE transport.

## Quick Start

### 1. Start the MCP Server

Run the startup script from the project root:

```bash
./scripts/start_mcp_server.sh
```

Or manually:

```bash
cd katana_mcp_server
uv run python -m katana_mcp --transport sse --port 8765
```

The server will start on `http://127.0.0.1:8765/sse`

### 2. Configure Cursor IDE

The `.mcp.json` file in the project root is already configured to connect to the server:

```json
{
  "mcpServers": {
    "katana-erp": {
      "type": "sse",
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

### 3. Restart Cursor IDE

After starting the server, restart Cursor IDE to load the MCP configuration.

## Configuration Options

### Custom Port

To use a different port:

1. Start the server with custom port:

   ```bash
   ./scripts/start_mcp_server.sh --port 9000
   ```

1. Update `.mcp.json`:

   ```json
   "katana-erp": {
     "type": "sse",
     "url": "http://127.0.0.1:9000/sse"
   }
   ```

### Custom Host

To listen on all interfaces (for remote access):

```bash
./scripts/start_mcp_server.sh --host 0.0.0.0 --port 8765
```

**Security Note**: Only expose the server on public interfaces if you have proper
authentication/authorization in place.

### HTTP Transport

To use HTTP transport instead of SSE:

```bash
./scripts/start_mcp_server.sh --transport http
```

Then update `.mcp.json`:

```json
"katana-erp": {
  "type": "http",
  "url": "http://127.0.0.1:8765"
}
```

## Environment Variables

The server requires the following environment variables:

- `KATANA_API_KEY` (required): Your Katana API key
- `KATANA_BASE_URL` (optional): API base URL (default: `https://api.katanamrp.com/v1`)

Set them in your `.env` file or export them:

```bash
export KATANA_API_KEY=your-api-key-here
export KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional
```

## Troubleshooting

### Server won't start

1. Check that `KATANA_API_KEY` is set:

   ```bash
   echo $KATANA_API_KEY
   ```

1. Verify dependencies are installed:

   ```bash
   cd katana_mcp_server
   uv sync
   ```

1. Check if port is already in use:

   ```bash
   lsof -i :8765
   ```

### Cursor can't connect

1. Verify the server is running:

   ```bash
   curl http://127.0.0.1:8765/sse
   ```

1. Check the URL in `.mcp.json` matches the server URL

1. Restart Cursor IDE after configuration changes

1. Check Cursor's MCP server logs for connection errors

### Tools not appearing

1. Verify the server started successfully (check startup logs)

1. Ensure Cursor IDE has been restarted after configuration changes

1. Check that the MCP server appears in Cursor's MCP server list

## Development Mode

For development with hot-reload, see [DEVELOPMENT.md](docs/development.md).

## Production Deployment

For production deployment, consider:

- Running the server as a systemd service or similar
- Using a reverse proxy (nginx, Caddy) for HTTPS
- Implementing proper authentication/authorization
- Setting up monitoring and logging

See the [Docker documentation](docs/docker.md) for containerized deployment options.
