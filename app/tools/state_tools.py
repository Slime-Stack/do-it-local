"""State management tools for passing data between agents via ADK session state."""

import json

from google.adk.tools import ToolContext

from app.constants.state_keys import (
    DETECTION_RESULT_KEY,
    GENERATION_RESULT_KEY,
    PIPELINE_STATUS_KEY,
    RECOMMENDATION_RESULT_KEY,
    SCAN_RESULT_KEY,
)


def save_scan_result(tool_context: ToolContext, scan_result_json: str) -> dict:
    """Save the scanner's analysis results to session state.

    Args:
        scan_result_json: JSON with keys: services, databases, queues, caches,
            env_vars, external_apis, language_stack, file_tree_summary,
            config_files_read, existing_docker_compose, existing_ci_cd,
            existing_iac
    """
    try:
        tool_context.state[SCAN_RESULT_KEY] = json.loads(scan_result_json)
        tool_context.state[PIPELINE_STATUS_KEY] = "scanning_complete"
        return {"status": "success"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}


def read_scan_result(tool_context: ToolContext) -> dict:
    """Read the scanner's analysis results from session state."""
    result = tool_context.state.get(SCAN_RESULT_KEY)
    if not result:
        return {"status": "error", "error": "No scan result found"}
    return {"status": "success", "scan_result": json.dumps(result, indent=2)}


def save_detection_result(
    tool_context: ToolContext, detection_result_json: str
) -> dict:
    """Save the detector's analysis results to session state.

    Args:
        detection_result_json: JSON with keys: pii_fields, side_effect_services,
            compliance_flags, secret_placeholders, risk_summary
    """
    try:
        tool_context.state[DETECTION_RESULT_KEY] = json.loads(detection_result_json)
        tool_context.state[PIPELINE_STATUS_KEY] = "detecting_complete"
        return {"status": "success"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}


def read_detection_result(tool_context: ToolContext) -> dict:
    """Read the detector's analysis results from session state."""
    result = tool_context.state.get(DETECTION_RESULT_KEY)
    if not result:
        return {"status": "error", "error": "No detection result found"}
    return {"status": "success", "detection_result": json.dumps(result, indent=2)}


def save_recommendation_result(
    tool_context: ToolContext, recommendation_result_json: str
) -> dict:
    """Save the recommender's environment strategy to session state.

    Args:
        recommendation_result_json: JSON with keys: environment_strategy,
            local_services, managed_services, mocked_services, seed_strategy,
            ci_cd_recommendations, files_to_generate
    """
    try:
        tool_context.state[RECOMMENDATION_RESULT_KEY] = json.loads(
            recommendation_result_json
        )
        tool_context.state[PIPELINE_STATUS_KEY] = "recommending_complete"
        return {"status": "success"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}


def read_recommendation_result(tool_context: ToolContext) -> dict:
    """Read the recommender's environment strategy from session state."""
    result = tool_context.state.get(RECOMMENDATION_RESULT_KEY)
    if not result:
        return {"status": "error", "error": "No recommendation result found"}
    return {
        "status": "success",
        "recommendation_result": json.dumps(result, indent=2),
    }


def save_generation_result(
    tool_context: ToolContext, generation_result_json: str
) -> dict:
    """Save the generator's output to session state.

    Args:
        generation_result_json: JSON with keys: files_generated, branch_name,
            merge_request_url, summary
    """
    try:
        tool_context.state[GENERATION_RESULT_KEY] = json.loads(generation_result_json)
        tool_context.state[PIPELINE_STATUS_KEY] = "complete"
        return {"status": "success"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}


def read_generation_result(tool_context: ToolContext) -> dict:
    """Read the generator's output from session state."""
    result = tool_context.state.get(GENERATION_RESULT_KEY)
    if not result:
        return {"status": "error", "error": "No generation result found"}
    return {"status": "success", "generation_result": json.dumps(result, indent=2)}
