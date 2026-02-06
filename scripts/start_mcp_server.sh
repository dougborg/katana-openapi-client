#!/usr/bin/env bash
# Start Katana MCP Server with SSE transport for independent operation
#
# Usage:
#   ./scripts/start_mcp_server.sh [--port PORT] [--host HOST]
#
# Examples:
#   ./scripts/start_mcp_server.sh                    # Start on default port 8765
#   ./scripts/start_mcp_server.sh --port 9000        # Start on custom port
#   ./scripts/start_mcp_server.sh --host 0.0.0.0      # Listen on all interfaces

set -euo pipefail

# Default values
PORT="${MCP_PORT:-8765}"
HOST="${MCP_HOST:-127.0.0.1}"
TRANSPORT="sse"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port)
      PORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --transport)
      TRANSPORT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Start Katana MCP Server with SSE transport"
      echo ""
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --port PORT      Port to listen on (default: 8765)"
      echo "  --host HOST      Host to bind to (default: 127.0.0.1)"
      echo "  --transport TYPE Transport type: sse or http (default: sse)"
      echo "  -h, --help       Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  KATANA_API_KEY   Required: Your Katana API key"
      echo "  KATANA_BASE_URL  Optional: API base URL (default: https://api.katanamrp.com/v1)"
      echo "  MCP_PORT         Port to listen on (overridden by --port)"
      echo "  MCP_HOST         Host to bind to (overridden by --host)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Load .env file if it exists
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

# Check if port is already in use
if command -v lsof >/dev/null 2>&1; then
  if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "Error: Port $PORT is already in use"
    echo ""
    echo "Processes using port $PORT:"
    lsof -i :"$PORT" | head -5
    echo ""
    echo "Options:"
    echo "  1. Kill the existing process: kill $(lsof -ti :"$PORT" | head -1)"
    echo "  2. Use a different port: $0 --port 9000"
    echo "  3. Find and kill manually: lsof -ti :$PORT | xargs kill"
    exit 1
  fi
fi

echo "Starting Katana MCP Server..."
echo "  Transport: $TRANSPORT"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  URL: http://$HOST:$PORT/sse"
echo ""
echo "Configure Cursor to connect to: http://$HOST:$PORT/sse"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd katana_mcp_server
uv run python -m katana_mcp --transport "$TRANSPORT" --host "$HOST" --port "$PORT"

