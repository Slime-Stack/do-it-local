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


def _mcp_params():
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    return StreamableHTTPConnectionParams(
        url=f"{gitlab_url}/api/v4/mcp",
        timeout=30.0,
    )


def get_gitlab_mcp_tools():
    """Full MCP toolset — all available GitLab MCP tools."""
    return McpToolset(
        connection_params=_mcp_params(),
        header_provider=_gitlab_header_provider,
    )


def get_gitlab_mcp_generator_tools():
    """Filtered MCP toolset for Generator — only MR and issue creation."""
    return McpToolset(
        connection_params=_mcp_params(),
        tool_filter=["create_merge_request", "create_issue"],
        header_provider=_gitlab_header_provider,
    )
