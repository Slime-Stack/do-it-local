"""
Model configuration for Do It Local ADK agents.

All agents use Flash-tier models for speed and cost efficiency.
Toggle between stable (Gemini 2.5) and preview (Gemini 3) via MODEL_TIER env var.
"""
import os

MODEL_TIER = os.getenv("MODEL_TIER", "stable")

MODEL_REGISTRY = {
    "stable": {
        "fast": "gemini-2.5-flash",
    },
    "preview": {
        "fast": "gemini-3-flash-preview",
    },
}

_tier = MODEL_REGISTRY.get(MODEL_TIER, MODEL_REGISTRY["stable"])
FAST_MODEL = os.getenv("FAST_MODEL", _tier["fast"])


def get_model(role: str) -> str:
    """All agents use the same Flash model for this project."""
    return FAST_MODEL


def get_temperature(role: str) -> float:
    """Gemini 3.x: always 1.0. Gemini 2.5: role-specific."""
    if MODEL_TIER == "preview":
        return 1.0
    temps = {
        "scanner": 0.3,
        "detector": 0.3,
        "generator": 0.4,
    }
    return temps.get(role, 0.4)


def get_thinking_config(role: str):
    """Return thinking config for the current tier."""
    from google.genai import types

    if MODEL_TIER == "preview":
        levels = {
            "scanner": "medium",
            "detector": "high",
            "generator": "high",
        }
        return types.ThinkingConfig(thinking_level=levels.get(role, "medium"))

    budgets = {
        "scanner": 2048,
        "detector": 4096,
        "generator": 4096,
    }
    budget = budgets.get(role, 2048)
    return types.ThinkingConfig(thinking_budget=budget)
