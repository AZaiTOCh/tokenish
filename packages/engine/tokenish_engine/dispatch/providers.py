"""
Provider dispatch + Argus-style fallback chain.

Order: Gemini (primary + alt models) → OpenRouter
OpenAI / Anthropic removed from the product surface.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from tokenish_engine.config import gemini_key, groq_key, openrouter_key, settings
from tokenish_engine.dispatch.argus import run_preflight
from tokenish_engine.models import ProviderStatus

_ROUTING_PATH = Path(__file__).resolve().parent.parent / "routing.json"

# Per-model cooldowns (provider/model -> unix time until retry). Do NOT kill whole providers.
_MODEL_COOLDOWN: dict[str, float] = {}
_COOLDOWN_SECS = 90.0

_OR_SKIP_SUBSTRINGS = (
    "lyria",
    "content-safety",
    "whisper",
    "tts",
    "embed",
    "moderation",
    "hy3",
    "-vl:",
    "vl:",
)


def _cooldown_key(provider: str, model: str) -> str:
    return f"{provider}/{model}"


def _model_on_cooldown(provider: str, model: str) -> bool:
    import time

    until = _MODEL_COOLDOWN.get(_cooldown_key(provider, model), 0.0)
    return time.time() < until


def _set_model_cooldown(provider: str, model: str, seconds: float | None = None) -> None:
    import time

    _MODEL_COOLDOWN[_cooldown_key(provider, model)] = time.time() + (seconds or _COOLDOWN_SECS)


def _openrouter_roster_models() -> list[str]:
    """Chat-capable free models from routing roster, preferred first."""
    preferred = [
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "qwen/qwen3-coder:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        settings.openrouter_free_model,
    ]
    roster: list[str] = []
    try:
        data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
        roster = list(data.get("openrouter_free_roster", {}).get("verified_active", []) or [])
    except Exception:
        roster = []
    merged = list(dict.fromkeys([*preferred, *roster]))
    out: list[str] = []
    for mid in merged:
        low = mid.lower()
        # Meta-router picks random free upstream (often rate-limited); use concrete IDs.
        if mid.strip() == "openrouter/free":
            continue
        if any(s in low for s in _OR_SKIP_SUBSTRINGS):
            continue
        if _model_on_cooldown("openrouter", mid):
            continue
        out.append(mid)
    if not out:
        # Last resort: cooled models + meta-router
        for mid in merged:
            if mid.strip() == "openrouter/free" or not _model_on_cooldown("openrouter", mid):
                out.append(mid)
                if len(out) >= 3:
                    break
    return out or [settings.openrouter_free_model]


@dataclass
class StreamSession:
    """Filled when chat_stream successfully connects to a provider."""
    provider: str | None = None
    model: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


def _load_fallbacks() -> list[tuple[str, str]]:
    try:
        data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
        raw = data.get("tasks", {}).get("chat", {}).get("fallbacks", [])
        out: list[tuple[str, str]] = []
        for item in raw:
            if "/" not in item:
                continue
            prov, model = item.split("/", 1)
            out.append((prov, model))
        if out:
            return out
    except Exception:
        pass
    return [
        ("gemini", settings.gemini_model),
        ("openrouter", settings.openrouter_free_model),
    ]


def _first_active_fallback() -> tuple[str, str] | None:
    for prov, mdl in _load_fallbacks():
        if _provider_active(prov):
            return prov, mdl
    return None


def resolve_provider(provider: str | None, model: str | None, target_engine: str) -> str:
    if provider and provider != "auto":
        p = provider.lower().strip()
        if p in {"google"}:
            return "gemini"
        if p in {"pplx"}:
            return "perplexity"
        return p
    blob = f"{model or ''} {target_engine or ''}".lower()
    if "claude" in blob or "anthropic" in blob:
        return "anthropic"
    if "gemini" in blob or "google" in blob:
        return "gemini"
    if "perplexity" in blob or "sonar" in blob:
        return "perplexity"
    if "openrouter" in blob or ":free" in blob:
        return "openrouter"
    if any(x in blob for x in ("gpt", "openai", "o1", "o3", "o4", "chatgpt")):
        # OpenAI removed from UI; map to auto fallback chain.
        pass
    if "groq" in blob or "llama-3" in blob:
        if _provider_active("groq"):
            return "groq"
    active = _first_active_fallback()
    if active:
        return active[0]
    if gemini_key():
        return "gemini"
    if openrouter_key():
        return "openrouter"
    return "gemini"


def resolve_model(provider: str, model: str | None, target_engine: str) -> str:
    m = (model or target_engine or "").strip()
    if provider == "gemini":
        return settings.gemini_model  # always gemini-3.5-flash
    if provider == "openrouter":
        return settings.openrouter_free_model if not m or "gpt" in m.lower() or m.startswith("gemini") else m
    if provider == "openai":
        return settings.openai_primary_model
    return m or target_engine or settings.gemini_model


def _provider_has_key(name: str) -> bool:
    if name == "groq":
        return bool(groq_key())
    if name == "gemini":
        return bool(gemini_key())
    if name == "openrouter":
        return bool(openrouter_key())
    if name == "perplexity":
        return bool(settings.perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY"))
    if name == "openai":
        return False  # removed from product surface
    if name == "anthropic":
        return False  # removed from product surface
    return False


def _provider_active(name: str) -> bool:
    if not _provider_has_key(name):
        return False
    try:
        data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
        prov = data.get("providers", {}).get(name, {})
        if "is_active" in prov:
            return bool(prov["is_active"])
    except Exception:
        pass
    return True


def _provider_ready(name: str) -> bool:
    return _provider_active(name)


async def preflight() -> list[ProviderStatus]:
    """Argus live health + key roster (Groq 70B/8B, Gemini 3.5, OpenRouter free)."""
    statuses, _ = await run_preflight()
    return statuses


async def preflight_full() -> tuple[list[ProviderStatus], dict]:
    return await run_preflight()


def _mark_provider_error(name: str, err: str, *, model: str | None = None) -> None:
    """
    Record failures without nuking the whole provider on a single free-model 429.
    OpenRouter: cooldown that model only. Gemini 503: transient, keep active.
    Gemini hard quota 429: mark inactive until key/billing recovers.
    """
    err_l = (err or "").lower()
    is_429 = "429" in err_l or "rate" in err_l
    is_503 = "503" in err_l or "high demand" in err_l
    is_402 = "402" in err_l or "credit" in err_l

    if name == "openrouter":
        if model:
            _set_model_cooldown("openrouter", model, 120 if is_429 or is_503 else 60)
        # Keep provider active so other free models can be tried.
        try:
            data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
            prov = data.setdefault("providers", {}).setdefault("openrouter", {})
            prov["is_active"] = True
            prov["error"] = (f"{model}: {err}" if model else err)[:160]
            _ROUTING_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
        return

    if name == "gemini":
        if is_503:
            _set_model_cooldown("gemini", settings.gemini_model, 45)
            try:
                data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
                prov = data.setdefault("providers", {}).setdefault("gemini", {})
                prov["is_active"] = True  # key still valid; spike is transient
                prov["error"] = err[:160]
                _ROUTING_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass
            return
        if is_429 or "quota" in err_l:
            try:
                data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
                prov = data.setdefault("providers", {}).setdefault("gemini", {})
                prov["is_active"] = False
                prov["error"] = err[:160]
                _ROUTING_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass
        return

    if not (is_402 or is_429 or "quota" in err_l or "credit" in err_l):
        return
    try:
        data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
        prov = data.setdefault("providers", {}).setdefault(name, {})
        prov["is_active"] = False
        prov["error"] = err[:160]
        _ROUTING_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def _provider_usable(name: str) -> bool:
    """Key present and not hard-disabled (OpenRouter stays usable if keyed)."""
    if not _provider_has_key(name):
        return False
    if name == "openrouter":
        return True
    if name == "gemini":
        # Allow gemini attempt even if last ping said inactive, unless quota error.
        try:
            data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
            err = str(data.get("providers", {}).get("gemini", {}).get("error") or "").lower()
            if "quota" in err and "429" in err:
                return False
        except Exception:
            pass
        return True
    return _provider_active(name)


def _completion_body(model: str, messages: list, *, provider: str, stream: bool) -> dict[str, Any]:
    max_tokens = 2048 if provider == "openrouter" else 4096
    body: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if stream:
        body["stream"] = True
    return body


def _user_content(envelope: str, image_b64: str | None, image_mime: str | None) -> Any:
    if image_b64:
        return [
            {"type": "text", "text": envelope},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image_mime or 'image/png'};base64,{image_b64}"},
            },
        ]
    return envelope


def _fallback_chain(provider: str, model: str) -> list[tuple[str, str]]:
    # Force Gemini requests onto gemini-3.5-flash only (never other Gemini IDs).
    if provider == "gemini" or (model or "").startswith("gemini"):
        provider, model = "gemini", settings.gemini_model
    if provider == "auto":
        provider, model = "gemini", settings.gemini_model

    chain: list[tuple[str, str]] = []
    if _provider_usable("gemini") and not _model_on_cooldown("gemini", settings.gemini_model):
        chain.append(("gemini", settings.gemini_model))

    # Expand OpenRouter into many free chat models (skip cooled-down ones).
    if openrouter_key():
        for mid in _openrouter_roster_models()[:10]:
            item = ("openrouter", mid)
            if item not in chain:
                chain.append(item)

    # Honor explicit non-auto request first if usable
    if provider not in {"auto", "gemini"} and _provider_usable(provider):
        first = (provider, model)
        chain = [first] + [x for x in chain if x != first]

    if provider == "gemini" and ("gemini", settings.gemini_model) in chain:
        # keep gemini first
        chain = [("gemini", settings.gemini_model)] + [x for x in chain if x[0] != "gemini"]

    seen: set[tuple[str, str]] = set()
    uniq: list[tuple[str, str]] = []
    for item in chain:
        if item in seen:
            continue
        if _model_on_cooldown(item[0], item[1]):
            continue
        seen.add(item)
        uniq.append(item)
    if uniq:
        return uniq
    if openrouter_key():
        return [("openrouter", settings.openrouter_free_model)]
    return [("gemini", settings.gemini_model)]


async def chat_complete(
    *,
    provider: str,
    model: str,
    envelope: str,
    history: list[dict[str, str]] | None = None,
    image_b64: str | None = None,
    image_mime: str | None = None,
) -> str:
    history = history or []
    errors: list[str] = []
    for prov, mdl in _fallback_chain(provider, model):
        try:
            return await _dispatch_once(
                provider=prov,
                model=mdl,
                envelope=envelope,
                history=history,
                image_b64=image_b64,
                image_mime=image_mime,
            )
        except Exception as exc:
            errors.append(f"{prov}/{mdl}: {exc}")
            _mark_provider_error(prov, str(exc), model=mdl)
            continue
    raise RuntimeError("all providers failed — " + " | ".join(errors[:6]))


def _provider_skip_reason(name: str) -> str:
    try:
        data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
        prov = data.get("providers", {}).get(name, {})
        err = prov.get("error") or ""
        if err:
            return f"{name}: {err}"
        if prov.get("is_active") is False:
            return f"{name}: unavailable"
    except Exception:
        pass
    if not _provider_has_key(name):
        return f"{name}: API key missing"
    return f"{name}: unavailable"


async def chat_stream(
    *,
    provider: str,
    model: str,
    envelope: str,
    history: list[dict[str, str]] | None = None,
    image_b64: str | None = None,
    image_mime: str | None = None,
    session: StreamSession | None = None,
) -> AsyncIterator[str]:
    history = history or []
    requested = (provider, model)
    chain = _fallback_chain(provider, model)
    last_err = ""
    errors: list[str] = []
    if chain and chain[0] != requested:
        last_err = _provider_skip_reason(requested[0])
    for prov, mdl in chain:
        try:
            if prov in {"openai", "groq", "openrouter", "perplexity"}:
                async for delta in _openai_compatible_stream(
                    provider=prov,
                    base_url=_base_url(prov),
                    api_key=_api_key(prov) or "",
                    model=mdl,
                    envelope=envelope,
                    history=history,
                    image_b64=image_b64 if prov in {"openai", "openrouter"} else None,
                    image_mime=image_mime if prov in {"openai", "openrouter"} else None,
                    extra_headers=_extra_headers(prov),
                ):
                    if session and session.provider is None:
                        session.provider = prov
                        session.model = mdl
                        session.fallback_used = (prov, mdl) != requested
                        if session.fallback_used and last_err:
                            session.fallback_reason = last_err
                        last_err = ""
                    yield delta
                if session and session.provider is None:
                    session.provider = prov
                    session.model = mdl
                    session.fallback_used = (prov, mdl) != requested
                    if session.fallback_used and last_err:
                        session.fallback_reason = last_err
                return
            text = await _dispatch_once(
                provider=prov,
                model=mdl,
                envelope=envelope,
                history=history,
                image_b64=image_b64,
                image_mime=image_mime,
            )
            if session:
                session.provider = prov
                session.model = mdl
                session.fallback_used = (prov, mdl) != requested
                if session.fallback_used and last_err:
                    session.fallback_reason = last_err
            yield text
            return
        except Exception as exc:
            last_err = f"{prov}/{mdl}: {str(exc)[:160]}"
            errors.append(last_err)
            _mark_provider_error(prov, str(exc), model=mdl)
            if session:
                session.fallback_reason = last_err
            continue
    detail = " | ".join(errors[:5]) if errors else last_err
    raise RuntimeError("all providers failed during stream" + (f" — {detail}" if detail else ""))


def _base_url(provider: str) -> str:
    if provider == "groq":
        return "https://api.groq.com/openai/v1"
    if provider == "openrouter":
        return "https://openrouter.ai/api/v1"
    if provider == "perplexity":
        return "https://api.perplexity.ai"
    return "https://api.openai.com/v1"


def _api_key(provider: str) -> str | None:
    if provider == "groq":
        return groq_key()
    if provider == "openrouter":
        return openrouter_key()
    if provider == "perplexity":
        return settings.perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
    if provider == "gemini":
        return gemini_key()
    return None


def _extra_headers(provider: str) -> dict[str, str]:
    if provider == "openrouter":
        return {
            "HTTP-Referer": "https://github.com/AZaiTOCh/tokenish",
            "X-Title": "tokenish",
        }
    return {}


async def _dispatch_once(
    *,
    provider: str,
    model: str,
    envelope: str,
    history: list[dict[str, str]],
    image_b64: str | None,
    image_mime: str | None,
) -> str:
    if provider == "anthropic":
        return await _anthropic_chat(model, envelope, history, image_b64, image_mime)
    if provider == "gemini":
        return await _gemini_chat(model, envelope, history, image_b64, image_mime)
    if provider in {"groq", "openai", "openrouter", "perplexity"}:
        return await _openai_compatible(
            provider=provider,
            base_url=_base_url(provider),
            api_key=_api_key(provider) or "",
            model=model,
            envelope=envelope,
            history=history,
            image_b64=image_b64 if provider in {"openai", "openrouter"} else None,
            image_mime=image_mime if provider in {"openai", "openrouter"} else None,
            extra_headers=_extra_headers(provider),
        )
    raise RuntimeError(f"unknown provider: {provider}")


async def _openai_compatible(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    envelope: str,
    history: list[dict[str, str]],
    image_b64: str | None,
    image_mime: str | None,
    extra_headers: dict[str, str] | None = None,
) -> str:
    if not api_key:
        raise RuntimeError(f"API key missing for {base_url}")
    messages: list[dict[str, Any]] = [
        {"role": h["role"], "content": h["content"]} for h in history
    ]
    messages.append(
        {"role": "user", "content": _user_content(envelope, image_b64, image_mime)}
    )
    headers = {"Authorization": f"Bearer {api_key}", **(extra_headers or {})}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=_completion_body(model, messages, provider=provider, stream=False),
        )
        if r.status_code >= 400:
            err = f"HTTP {r.status_code}: {r.text[:240]}"
            _mark_provider_error(provider, err, model=model)
            raise RuntimeError(err)
        return r.json()["choices"][0]["message"]["content"]


async def _openai_compatible_stream(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    envelope: str,
    history: list[dict[str, str]],
    image_b64: str | None,
    image_mime: str | None,
    extra_headers: dict[str, str] | None = None,
) -> AsyncIterator[str]:
    if not api_key:
        raise RuntimeError(f"API key missing for {base_url}")
    messages: list[dict[str, Any]] = [
        {"role": h["role"], "content": h["content"]} for h in history
    ]
    messages.append(
        {"role": "user", "content": _user_content(envelope, image_b64, image_mime)}
    )
    headers = {"Authorization": f"Bearer {api_key}", **(extra_headers or {})}
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=_completion_body(model, messages, provider=provider, stream=True),
        ) as r:
            if r.status_code >= 400:
                body = await r.aread()
                err = f"HTTP {r.status_code}: {body[:240]!r}"
                _mark_provider_error(provider, err, model=model)
                raise RuntimeError(err)
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    data = json.loads(payload)
                    delta = data["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except Exception:
                    continue


async def _gemini_chat(
    model: str,
    envelope: str,
    history: list[dict[str, str]],
    image_b64: str | None = None,
    image_mime: str | None = None,
) -> str:
    key = gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY / GOOGLE_API_KEY missing")
    contents = []
    for h in history:
        role = "user" if h["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h["content"]}]})
    user_parts: list[dict[str, Any]] = []
    if image_b64:
        user_parts.append(
            {
                "inline_data": {
                    "mime_type": image_mime or "image/jpeg",
                    "data": image_b64,
                }
            }
        )
    user_parts.append({"text": envelope})
    contents.append({"role": "user", "parts": user_parts})

    async def _call(mdl: str) -> httpx.Response:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{mdl}:generateContent?key={key}"
        )
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2},
        }
        if "Execute#D_Only" in envelope or "DoNotRewriteOrSummarize#D" in envelope:
            body["systemInstruction"] = {
                "parts": [
                    {
                        "text": (
                            "Execute the attached document (#D) exactly. "
                            "Do not rewrite, summarize, or reproduce #D. "
                            "Reply with only what #D instructs you to produce."
                        )
                    }
                ]
            }
        async with httpx.AsyncClient(timeout=120.0) as client:
            return await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
            )

    r = await _call(settings.gemini_model if model.startswith("gemini") else model)
    # Never fall back to other Gemini versions — only surface the HTTP error
    # so the outer chain can try OpenRouter.
    if r.status_code >= 400:
        raise RuntimeError(f"gemini HTTP {r.status_code}: {r.text[:240]}")
    data = r.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


async def _anthropic_chat(
    model: str,
    envelope: str,
    history: list[dict[str, str]],
    image_b64: str | None,
    image_mime: str | None,
) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY missing")
    messages: list[dict[str, Any]] = []
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    if image_b64:
        content: Any = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_mime or "image/png",
                    "data": image_b64,
                },
            },
            {"type": "text", "text": envelope},
        ]
    else:
        content = envelope
    messages.append({"role": "user", "content": content})
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": model, "max_tokens": 4096, "messages": messages},
        )
        if r.status_code >= 400:
            raise RuntimeError(f"anthropic HTTP {r.status_code}: {r.text[:240]}")
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
