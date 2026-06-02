"""Model configuration for Do It Local ADK agents.

Two tiers matching SlimeStudio conventions:
- stable (default): Gemini 3.5 Flash (GA, best agentic performance)
- preview: Gemini 2.5 Flash (fallback)
"""

import os

MODEL_TIER = os.getenv("MODEL_TIER", "stable")

MODEL_REGISTRY = {
    "stable": {
        "flash": "gemini-3.5-flash",
    },
    "preview": {
        "flash": "gemini-2.5-flash",
    },
}

_tier = MODEL_REGISTRY.get(MODEL_TIER, MODEL_REGISTRY["stable"])
FLASH_MODEL = os.getenv("FLASH_MODEL", _tier["flash"])


def get_model(role: str) -> str:
    return FLASH_MODEL


def get_temperature(role: str) -> float:
    if MODEL_TIER == "stable":
        return 1.0
    return {"scanner": 0.3, "detector": 0.3, "generator": 0.4}.get(role, 0.4)


def get_thinking_config(role: str):
    from google.genai import types

    if MODEL_TIER == "stable":
        levels = {"scanner": "medium", "detector": "high", "generator": "high"}
        return types.ThinkingConfig(thinking_level=levels.get(role, "medium"))

    budgets = {"scanner": 2048, "detector": 4096, "generator": 4096}
    return types.ThinkingConfig(thinking_budget=budgets.get(role, 2048))
