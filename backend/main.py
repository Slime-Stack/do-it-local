"""FastAPI application — Do It Local API."""

import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.auth import verify_api_key
from backend.models import PipelineRequest
from backend.pipeline_runner import stream_pipeline

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
    version="0.2.0",
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
    "/api/pipeline/stream",
    dependencies=[Depends(verify_api_key)],
)
async def pipeline_stream(request: PipelineRequest):
    if request.project_url.host not in _allowed_hosts():
        raise HTTPException(
            status_code=400,
            detail=f"Only GitLab URLs are allowed. Got host: {request.project_url.host}",
        )

    return StreamingResponse(
        stream_pipeline(
            project_url=str(request.project_url),
            gitlab_token=request.gitlab_token.get_secret_value(),
            mcp_token=request.mcp_token.get_secret_value(),
            target_branch=request.target_branch,
            environment_target=request.environment_target,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
