"""Convert ADK Event objects into simplified JSON dicts for SSE streaming.

Excludes session state values (which may contain the GitLab token) from
all output. Only surfaces agent names, tool calls, tool results, and text.
"""

import json

from app.constants.state_keys import (
    DETECTION_RESULT_KEY,
    GENERATION_RESULT_KEY,
    PIPELINE_STATUS_KEY,
    RECOMMENDATION_RESULT_KEY,
    SCAN_RESULT_KEY,
)

_SENSITIVE_STATE_KEYS = {"gitlab_token", "mcp_token"}


def format_event(event) -> dict | None:
    if hasattr(event, "actions") and event.actions:
        state_delta = getattr(event.actions, "state_delta", None) or {}

        if PIPELINE_STATUS_KEY in state_delta:
            status = state_delta[PIPELINE_STATUS_KEY]
            return {"type": "status", "status": status}

        # Also check escalation — when a new sub-agent starts
        if state_delta:
            import logging

            logging.getLogger(__name__).debug(
                "state_delta keys: %s", list(state_delta.keys())
            )

    author = getattr(event, "author", None) or ""
    agent = author if isinstance(author, str) else str(author)

    content = getattr(event, "content", None)
    if not content:
        return None

    parts = getattr(content, "parts", None) or []
    for part in parts:
        function_call = getattr(part, "function_call", None)
        if function_call:
            return {
                "agent": agent,
                "type": "tool_call",
                "content": {
                    "name": function_call.name,
                    "args": _safe_args(function_call.args),
                },
            }

        function_response = getattr(part, "function_response", None)
        if function_response:
            return {
                "agent": agent,
                "type": "tool_result",
                "content": {
                    "name": function_response.name,
                    "result": _truncate(function_response.response),
                },
            }

        text = getattr(part, "text", None)
        if text and text.strip():
            return {
                "agent": agent,
                "type": "text",
                "content": text.strip(),
            }

    return None


def format_done(state: dict) -> dict:
    safe_state = {
        k: v
        for k, v in state.items()
        if k
        in {
            SCAN_RESULT_KEY,
            DETECTION_RESULT_KEY,
            RECOMMENDATION_RESULT_KEY,
            GENERATION_RESULT_KEY,
        }
    }
    return {"type": "done", "results": safe_state}


def _safe_args(args) -> dict:
    if not args:
        return {}
    if isinstance(args, dict):
        return {k: v for k, v in args.items() if k not in _SENSITIVE_STATE_KEYS}
    return {}


def _truncate(obj, max_len: int = 2000) -> str:
    try:
        s = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        s = str(obj)
    if len(s) > max_len:
        return s[:max_len] + "...(truncated)"
    return s
