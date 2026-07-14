"""
Linked API inventory — single source of truth for which providers have keys.

Used by /settings/keys (popup greying) and Argus preflight readiness.
Mirrors load order of config key helpers: ~/.tokenish config → env → Settings/.env.
Never invents keys; never returns secret values.
"""

from __future__ import annotations

from typing import Any

from tokenish_engine.config import (
    anthropic_key,
    gemini_key,
    grok_key,
    groq_key,
    openai_key,
    openrouter_key,
    perplexity_key,
)
from tokenish_engine.settings_store import apply_saved_keys_to_environ


# Stable order for UI + Argus reporting.
PROVIDER_ORDER: tuple[str, ...] = (
    "gemini",
    "openrouter",
    "openai",
    "anthropic",
    "perplexity",
    "grok",
    "groq",
)


def linked_provider_status() -> dict[str, bool]:
    """Which chat providers already have a usable API key."""
    apply_saved_keys_to_environ(overwrite=True)
    return {
        "gemini": bool(gemini_key()),
        "openrouter": bool(openrouter_key()),
        "openai": bool(openai_key()),
        "anthropic": bool(anthropic_key()),
        "perplexity": bool(perplexity_key()),
        "groq": bool(groq_key()),
        "grok": bool(grok_key()),
    }


def linked_inventory() -> dict[str, Any]:
    """Factual inventory block for Argus /providers meta (no secrets)."""
    has = linked_provider_status()
    linked = [name for name in PROVIDER_ORDER if has.get(name)]
    return {
        "has": has,
        "linked": linked,
        "linked_count": len(linked),
        "any_linked": bool(linked),
    }
