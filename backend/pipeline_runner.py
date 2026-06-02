"""Async ADK pipeline execution."""

import asyncio
import logging

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.constants.state_keys import (
    DETECTION_RESULT_KEY,
    GENERATION_RESULT_KEY,
    PIPELINE_STATUS_KEY,
    PROJECT_URL_KEY,
    SCAN_RESULT_KEY,
    TARGET_BRANCH_KEY,
)
from app.tools.gitlab_rest import clear_token, set_token
from backend.job_store import update_job

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(2)


async def run_pipeline(
    job_id: str,
    project_url: str,
    gitlab_token: str,
    target_branch: str = "main",
) -> None:
    """Run the full Scanner -> Detector -> Generator pipeline."""
    user_id = f"job-{job_id}"
    async with _semaphore:
        try:
            update_job(job_id, status="scanning")
            set_token(user_id, gitlab_token)

            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="do_it_local",
                user_id=user_id,
                state={
                    PROJECT_URL_KEY: project_url,
                    TARGET_BRANCH_KEY: target_branch,
                    PIPELINE_STATUS_KEY: "scanning",
                },
            )

            runner = Runner(
                agent=root_agent,
                app_name="do_it_local",
                session_service=session_service,
            )

            trigger = f"Analyze the GitLab project at {project_url} and generate local dev environment configuration. Target branch: {target_branch}"

            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=trigger)],
                ),
            ):
                if hasattr(event, "actions") and event.actions:
                    state = (
                        event.actions.state_delta
                        if hasattr(event.actions, "state_delta")
                        else {}
                    )
                    if PIPELINE_STATUS_KEY in state:
                        status = state[PIPELINE_STATUS_KEY]
                        if status == "scanning_complete":
                            update_job(job_id, status="detecting")
                        elif status == "detecting_complete":
                            update_job(job_id, status="generating")

            final_session = await session_service.get_session(
                app_name="do_it_local",
                user_id=session.user_id,
                session_id=session.id,
            )

            state = final_session.state if final_session else {}
            update_job(
                job_id,
                status="complete",
                scan_result=state.get(SCAN_RESULT_KEY),
                detection_result=state.get(DETECTION_RESULT_KEY),
                generation_result=state.get(GENERATION_RESULT_KEY),
            )

            logger.info("Pipeline complete for job %s", job_id)

        except Exception as e:
            logger.exception("Pipeline failed for job %s", job_id)
            update_job(job_id, status="error", error=str(e))
        finally:
            clear_token(user_id)
