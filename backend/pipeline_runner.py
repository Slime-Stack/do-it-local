"""Async ADK pipeline execution — SSE streaming generator."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator

import gitlab
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.constants.state_keys import (
    ENVIRONMENT_TARGET_KEY,
    GITLAB_TOKEN_KEY,
    MCP_TOKEN_KEY,
    PIPELINE_STATUS_KEY,
    PROJECT_URL_KEY,
    TARGET_BRANCH_KEY,
)
from backend.event_formatter import format_done, format_event

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(1)


def _fetch_repo_tree(project_url: str, gitlab_token: str) -> str:
    """Pre-fetch the repo tree via REST so agents don't have to."""
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")

    if gitlab_token.startswith("glpat-"):
        gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
    else:
        gl = gitlab.Gitlab(gitlab_url, oauth_token=gitlab_token)

    path = project_url.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    for prefix in [f"{gitlab_url}/", "https://gitlab.com/", "http://gitlab.com/"]:
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break

    project = gl.projects.get(path)
    items = project.repository_tree(recursive=True, per_page=100, get_all=True)
    tree_lines = [f"  {item['type'][0]} {item['path']}" for item in items]
    return "\n".join(tree_lines)


async def stream_pipeline(
    project_url: str,
    gitlab_token: str,
    mcp_token: str,
    target_branch: str = "main",
    environment_target: str = "local",
) -> AsyncGenerator[str, None]:
    """Run the pipeline and yield SSE-formatted event strings."""
    async with _semaphore:
        # Pre-fetch repo tree so Scanner doesn't need a round-trip
        try:
            repo_tree = await asyncio.to_thread(
                _fetch_repo_tree, project_url, gitlab_token
            )
        except Exception as e:
            logger.error("Failed to pre-fetch repo tree: %s", e)
            repo_tree = (
                "(Could not fetch repo tree — Scanner should use list_repo_tree tool)"
            )

        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="do_it_local",
            user_id="sse-user",
            state={
                PROJECT_URL_KEY: project_url,
                TARGET_BRANCH_KEY: target_branch,
                ENVIRONMENT_TARGET_KEY: environment_target,
                GITLAB_TOKEN_KEY: gitlab_token,
                MCP_TOKEN_KEY: mcp_token,
                PIPELINE_STATUS_KEY: "scanning",
            },
        )

        runner = Runner(
            agent=root_agent,
            app_name="do_it_local",
            session_service=session_service,
        )

        trigger = (
            f"Analyze the GitLab project at {project_url} and generate "
            f"environment configuration. Target branch: {target_branch}. "
            f"Environment target: {environment_target}.\n\n"
            f"## Repository Tree\n{repo_tree}"
        )

        heartbeat_count = 0

        try:
            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=trigger)],
                ),
            ):
                formatted = format_event(event)
                if formatted:
                    yield f"data: {json.dumps(formatted)}\n\n"
                else:
                    heartbeat_count += 1
                    if heartbeat_count % 10 == 0:
                        yield ": heartbeat\n\n"

            final_session = await session_service.get_session(
                app_name="do_it_local",
                user_id=session.user_id,
                session_id=session.id,
            )
            state = final_session.state if final_session else {}
            done_event = format_done(state)
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            logger.exception("Pipeline failed")
            error_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

        finally:
            if session:
                final = await session_service.get_session(
                    app_name="do_it_local",
                    user_id=session.user_id,
                    session_id=session.id,
                )
                if final:
                    for key in (GITLAB_TOKEN_KEY, MCP_TOKEN_KEY):
                        if key in final.state:
                            final.state[key] = ""
