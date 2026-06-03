"""Async ADK pipeline execution — SSE streaming generator."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.constants.state_keys import (
    GITLAB_TOKEN_KEY,
    MCP_TOKEN_KEY,
    PIPELINE_STATUS_KEY,
    PROJECT_URL_KEY,
    TARGET_BRANCH_KEY,
)
from backend.event_formatter import format_done, format_event

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(2)


async def stream_pipeline(
    project_url: str,
    gitlab_token: str,
    mcp_token: str,
    target_branch: str = "main",
) -> AsyncGenerator[str, None]:
    """Run the pipeline and yield SSE-formatted event strings."""
    async with _semaphore:
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="do_it_local",
            user_id="sse-user",
            state={
                PROJECT_URL_KEY: project_url,
                TARGET_BRANCH_KEY: target_branch,
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
            f"local dev environment configuration. Target branch: {target_branch}"
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
