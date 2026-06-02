"""GitLab MCP server integration for semantic search and MR creation.

Uses mcp-remote to proxy the HTTP-based GitLab MCP endpoint over stdio.
Auth is via OAuth 2.0 browser flow (no PAT needed for MCP).

See: https://docs.gitlab.com/user/gitlab_duo/model_context_protocol/mcp_server/
"""

import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


def get_gitlab_mcp_tools():
    """Create MCPToolset for GitLab MCP server. Requires Node.js 20+."""
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    mcp_endpoint = f"{gitlab_url}/api/v4/mcp"

    return MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote", mcp_endpoint],
        ),
        tool_filter=["semantic_code_search", "search", "create_merge_request"],
    )
