"""GitLab MCP server integration for semantic search and MR creation.

Uses ADK's MCPToolset to connect to the GitLab MCP server via stdio.
Provides semantic_code_search and create_merge_request tools.
"""
import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


def get_gitlab_mcp_tools():
    """Create MCPToolset for GitLab MCP server.

    Requires:
    - npx (Node.js) installed
    - GITLAB_PERSONAL_ACCESS_TOKEN env var set
    - GITLAB_API_URL env var (defaults to https://gitlab.com/api/v4)
    """
    token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN", "")
    api_url = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")

    return MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@gitlab-org/gitlab-mcp-server"],
            env={
                "GITLAB_PERSONAL_ACCESS_TOKEN": token,
                "GITLAB_API_URL": api_url,
            },
        ),
        # Only expose the tools we need from the 15 available
        tool_filter=[
            "semantic_code_search",
            "search",
            "create_merge_request",
        ],
    )
