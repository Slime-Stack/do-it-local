"""Request/response Pydantic models."""

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class EnvironmentTarget(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    BOTH = "both"


class PipelineRequest(BaseModel):
    project_url: HttpUrl
    gitlab_token: SecretStr = Field(
        ...,
        description="GitLab PAT with api scope for REST operations.",
    )
    mcp_token: SecretStr = Field(
        ...,
        description="GitLab OAuth token with mcp scope for MCP operations.",
    )
    target_branch: str = "main"
    environment_target: EnvironmentTarget = EnvironmentTarget.LOCAL
