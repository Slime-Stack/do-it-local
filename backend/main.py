"""FastAPI application — Do It Local API."""

import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

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
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    logger.info("Do It Local API starting")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Do It Local",
    description="AI-powered local dev environment generator",
    version="0.1.0",
    lifespan=lifespan,
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _allowed_hosts() -> set[str]:
    hosts = {"gitlab.com"}
    custom = os.getenv("GITLAB_URL", "")
    if custom:
        parsed = urlparse(custom)
        if parsed.hostname:
            hosts.add(parsed.hostname)
    return hosts


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.post(
    "/api/jobs",
    response_model=CreateJobResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_analysis_job(
    request: CreateJobRequest, background_tasks: BackgroundTasks
):
    if request.project_url.host not in _allowed_hosts():
        raise HTTPException(
            status_code=400,
            detail=f"Only GitLab URLs are allowed. Got host: {request.project_url.host}",
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


@app.get(
    "/api/jobs/{job_id}",
    response_model=JobStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return JobStatusResponse(
            job_id=job_id, status=JobStatus.ERROR, error="Job not found"
        )
    return JobStatusResponse(
        job_id=job_id, status=JobStatus(job["status"]), error=job.get("error")
    )


@app.get(
    "/api/jobs/{job_id}/results",
    response_model=JobResultsResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_job_results(job_id: str):
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


_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
