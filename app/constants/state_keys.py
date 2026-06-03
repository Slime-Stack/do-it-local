"""State key constants for ADK session state.

GitLab token is safe in session state — we use InMemorySessionService only.
If we ever switch to a persistent session service, move token back to
an in-memory store pattern.
"""

PROJECT_URL_KEY = "project_url"
TARGET_BRANCH_KEY = "target_branch"
ENVIRONMENT_TARGET_KEY = "environment_target"
GITLAB_TOKEN_KEY = "gitlab_token"
MCP_TOKEN_KEY = "mcp_token"
SCAN_RESULT_KEY = "scan_result"
DETECTION_RESULT_KEY = "detection_result"
RECOMMENDATION_RESULT_KEY = "recommendation_result"
GENERATION_RESULT_KEY = "generation_result"
PIPELINE_STATUS_KEY = "pipeline_status"
