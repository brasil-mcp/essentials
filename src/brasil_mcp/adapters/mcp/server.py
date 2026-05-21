"""Entry point: brasil-mcp-server — MCP server stdio."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from brasil_mcp.adapters.mcp.tools import register_tools
from brasil_mcp.core.telemetry import maybe_show_notice


def build_server() -> FastMCP:
    """Constrói um FastMCP server com todas as 14 tools registradas."""
    mcp = FastMCP("brasil-mcp-essentials")
    register_tools(mcp)
    return mcp


def main() -> None:
    """Entry point chamado pelo console_script brasil-mcp-server."""
    maybe_show_notice()
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
