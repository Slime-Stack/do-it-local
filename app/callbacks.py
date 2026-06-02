"""ADK agent callbacks for structured logging."""
import json
import logging
import time

logger = logging.getLogger(__name__)

_call_timers: dict[str, float] = {}


def _timer_key(callback_context) -> str:
    return f"{callback_context.agent_name}:{callback_context.invocation_id}"


def before_model_callback(callback_context, llm_request):
    """Record call start time."""
    _call_timers[_timer_key(callback_context)] = time.monotonic()
    return None


def after_model_callback(callback_context, llm_response):
    """Log structured agent call data after LLM response."""
    agent_name = callback_context.agent_name or "unknown"
    key = _timer_key(callback_context)

    start = _call_timers.pop(key, None)
    latency_ms = int((time.monotonic() - start) * 1000) if start else None

    usage = {}
    if llm_response.usage_metadata:
        meta = llm_response.usage_metadata
        usage = {
            "prompt_tokens": getattr(meta, "prompt_token_count", None),
            "candidates_tokens": getattr(meta, "candidates_token_count", None),
            "total_tokens": getattr(meta, "total_token_count", None),
        }

    log_entry = {
        "event": "agent_call",
        "agent": agent_name,
        "latency_ms": latency_ms,
        **usage,
    }

    logger.info("agent_call: %s", json.dumps(log_entry))
    return None
