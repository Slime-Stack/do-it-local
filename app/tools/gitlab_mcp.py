"""GitLab MCP integration via McpToolset with header_provider.

Uses StreamableHTTPConnectionParams to connect directly to GitLab's
MCP endpoint. Auth is injected per-session via header_provider reading
the GitLab token from ADK session state.
"""

import os

from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)


def _gitlab_header_provider(ctx):
    token = ctx.state.get("mcp_token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_gitlab_mcp_tools():
    """Create McpToolset for GitLab MCP server."""
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    mcp_endpoint = f"{gitlab_url}/api/v4/mcp"

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=mcp_endpoint,
            timeout=30.0,
        ),
        header_provider=_gitlab_header_provider,
    )
