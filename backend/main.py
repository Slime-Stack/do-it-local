"""FastAPI application — Do It Local API."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth import verify_api_key
from backend.job_store import create_job, get_job
from backend.models import (
    CreateJobRequest,
    CreateJobResponse,
    JobResultsResponse,
    JobStatus,
    JobStatusResponse,
)
from backend.pipeline_runner import run_pipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and graceful shutdown."""
    # Configure structured logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    logger.info("Do It Local API starting")

    yield

    # Graceful shutdown: mark in-progress jobs as interrupted
    logger.info("Shutting down — marking in-progress jobs as interrupted")


app = FastAPI(
    title="Do It Local",
    description="AI-powered local dev environment generator",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """Readiness probe — checks dependencies."""
    # TODO: check Firestore connectivity
    return {"status": "ready"}


@app.post("/api/jobs", response_model=CreateJobResponse, dependencies=[Depends(verify_api_key)])
async def create_analysis_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
):
    """Create a new analysis job. Returns immediately with job_id."""
    # SSRF protection: only allow known GitLab hosts
    allowed_hosts = {"gitlab.com"}
    custom_host = os.getenv("GITLAB_URL", "")
    if custom_host:
        from urllib.parse import urlparse

        parsed = urlparse(custom_host)
        if parsed.hostname:
            allowed_hosts.add(parsed.hostname)

    url_host = request.project_url.host
    if url_host not in allowed_hosts:
        raise HTTPException(
            status_code=400,
            detail=f"Only GitLab URLs are allowed. Got host: {url_host}",
        )

    job_id = create_job(
        project_url=str(request.project_url),
        target_branch=request.target_branch,
    )

    background_tasks.add_task(
        run_pipeline,
        job_id=job_id,
        project_url=str(request.project_url),
        gitlab_token=request.gitlab_token.get_secret_value(),
        target_branch=request.target_branch,
    )

    return CreateJobResponse(job_id=job_id, status=JobStatus.PENDING)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(verify_api_key)])
async def get_job_status(job_id: str):
    """Poll job status."""
    job = get_job(job_id)
    if not job:
        return JobStatusResponse(job_id=job_id, status=JobStatus.ERROR, error="Job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        error=job.get("error"),
    )


@app.get("/api/jobs/{job_id}/results", response_model=JobResultsResponse, dependencies=[Depends(verify_api_key)])
async def get_job_results(job_id: str):
    """Get full job results."""
    job = get_job(job_id)
    if not job:
        return JobResultsResponse(job_id=job_id, status=JobStatus.ERROR)
    return JobResultsResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        scan_result=job.get("scan_result"),
        detection_result=job.get("detection_result"),
        generation_result=job.get("generation_result"),
    )


# Serve frontend static files in production
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
