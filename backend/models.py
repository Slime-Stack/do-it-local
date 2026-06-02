"""Request/response Pydantic models."""
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class JobStatus(StrEnum):
    PENDING = "pending"
    SCANNING = "scanning"
    DETECTING = "detecting"
    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"


class CreateJobRequest(BaseModel):
    project_url: HttpUrl
    gitlab_token: SecretStr = Field(
        ...,
        description="GitLab PAT with api scope. Never logged or returned.",
    )
    target_branch: str = "main"


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None


class JobResultsResponse(BaseModel):
    job_id: str
    status: JobStatus
    scan_result: dict | None = None
    detection_result: dict | None = None
    generation_result: dict | None = None
