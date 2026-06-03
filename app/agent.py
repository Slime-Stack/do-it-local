"""Do It Local — ADK Agent Definitions.

Sequential pipeline: Scanner -> Detector -> Recommender -> Generator
"""

import os

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.genai import types

from .callbacks import after_model_callback, before_model_callback
from .config import get_model, get_temperature, get_thinking_config
from .prompts import (
    DETECTOR_INSTRUCTION,
    GENERATOR_INSTRUCTION,
    RECOMMENDER_INSTRUCTION,
    SCANNER_INSTRUCTION,
)
from .tools import (
    commit_files,
    create_branch,
    get_gitlab_mcp_tools,
    read_detection_result,
    read_file,
    read_recommendation_result,
    read_scan_result,
    save_detection_result,
    save_generation_result,
    save_recommendation_result,
    save_scan_result,
)

if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
    import google.auth

    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or "")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

gitlab_mcp = get_gitlab_mcp_tools()

scanner_agent = Agent(
    name="scanner",
    model=get_model("scanner"),
    description="Scans repositories to identify services, databases, queues, env vars, and dependencies",
    instruction=SCANNER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=get_temperature("scanner"),
        thinking_config=get_thinking_config("scanner"),
    ),
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    tools=[read_file, save_scan_result, gitlab_mcp],
)

detector_agent = Agent(
    name="detector",
    model=get_model("detector"),
    description="Analyzes scan results to detect PII fields, side-effect services, and compliance concerns",
    instruction=DETECTOR_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=get_temperature("detector"),
        thinking_config=get_thinking_config("detector"),
    ),
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    tools=[read_scan_result, save_detection_result],
)

recommender_agent = Agent(
    name="recommender",
    model=get_model("recommender"),
    description="Proposes environment strategy: what to run locally, what to mock, what files to generate",
    instruction=RECOMMENDER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=get_temperature("recommender"),
        thinking_config=get_thinking_config("recommender"),
    ),
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    tools=[read_scan_result, read_detection_result, save_recommendation_result],
)

generator_agent = Agent(
    name="generator",
    model=get_model("generator"),
    description="Generates environment configs and delivers as GitLab merge request",
    instruction=GENERATOR_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=get_temperature("generator"),
        thinking_config=get_thinking_config("generator"),
    ),
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    tools=[
        read_scan_result,
        read_detection_result,
        read_recommendation_result,
        read_file,
        create_branch,
        commit_files,
        save_generation_result,
        gitlab_mcp,
    ],
)

root_agent = SequentialAgent(
    name="do_it_local_pipeline",
    description="Analyzes a GitLab repo and generates environment configuration",
    sub_agents=[scanner_agent, detector_agent, recommender_agent, generator_agent],
)
