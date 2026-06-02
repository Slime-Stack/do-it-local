"""GitLab MCP server integration for semantic search and MR creation.

Uses ADK's MCPToolset to connect to the GitLab MCP server via stdio.
The GitLab MCP server uses HTTP transport proxied through mcp-remote,
with OAuth 2.0 browser-based auth (no PAT needed for MCP — PAT is only
used by our REST API tools in gitlab_rest.py).

Available MCP tools we use:
- semantic_code_search: search code semantically in a project
- search: search across GitLab instance (issues, MRs, code, etc.)
- create_merge_request: create an MR (requires id, title, source_branch, target_branch)

See: https://docs.gitlab.com/user/gitlab_duo/model_context_protocol/mcp_server/
"""
import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


def get_gitlab_mcp_tools():
    """Create MCPToolset for GitLab MCP server.

    Uses mcp-remote to proxy the HTTP-based GitLab MCP endpoint over stdio,
    which is what ADK's MCPToolset expects.

    Requires:
    - Node.js 20+ installed (for npx)
    - First run will trigger OAuth browser flow for GitLab auth
    """
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    mcp_endpoint = f"{gitlab_url}/api/v4/mcp"

    return MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote", mcp_endpoint],
        ),
        tool_filter=[
            "semantic_code_search",
            "search",
            "create_merge_request",
        ],
    )
