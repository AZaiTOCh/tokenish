"""Fallback chain must keep OpenRouter alive across per-model 429s."""

from __future__ import annotations

from tokenish_engine.dispatch import providers as P


def test_openrouter_429_cools_model_not_provider(monkeypatch, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text(
        '{"providers":{"openrouter":{"is_active":true},"gemini":{"is_active":false,'
        '"error":"quota 429"}},"openrouter_free_roster":{"verified_active":['
        '"google/gemma-4-31b-it:free","openai/gpt-oss-120b:free","meta-llama/llama-3.2-3b-instruct:free"]}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(P, "_ROUTING_PATH", routing)
    monkeypatch.setattr(P, "_MODEL_COOLDOWN", {})
    monkeypatch.setattr(P, "openrouter_key", lambda: "sk-or-test")
    monkeypatch.setattr(P, "gemini_key", lambda: "")

    P._mark_provider_error(
        "openrouter",
        "HTTP 429: openai/gpt-oss-120b:free is temporarily rate-limited",
        model="openai/gpt-oss-120b:free",
    )
    data = __import__("json").loads(routing.read_text(encoding="utf-8"))
    assert data["providers"]["openrouter"]["is_active"] is True
    assert P._model_on_cooldown("openrouter", "openai/gpt-oss-120b:free")

    chain = P._fallback_chain("auto", "auto")
    models = [m for p, m in chain if p == "openrouter"]
    assert "openai/gpt-oss-120b:free" not in models
    assert any("gemma" in m or "llama" in m for m in models)
    assert len(models) >= 2


def test_fallback_skips_openrouter_free_meta(monkeypatch, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text(
        '{"providers":{"openrouter":{"is_active":true},"gemini":{"is_active":true}},'
        '"openrouter_free_roster":{"verified_active":["openrouter/free","google/gemma-4-31b-it:free"]}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(P, "_ROUTING_PATH", routing)
    monkeypatch.setattr(P, "_MODEL_COOLDOWN", {})
    monkeypatch.setattr(P, "openrouter_key", lambda: "sk-or-test")
    monkeypatch.setattr(P, "gemini_key", lambda: "gk-test")

    models = P._openrouter_roster_models()
    assert "openrouter/free" not in models
    assert "google/gemma-4-31b-it:free" in models
