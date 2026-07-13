from __future__ import annotations

from tokenish_engine.compile.tokenizer_gate import apply_if_cheaper
from tokenish_engine.meters.tokens import count_tokens


def _serialize(history: list[dict[str, str]]) -> str:
    return "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history)


def compress_history(
    history: list[dict[str, str]],
    *,
    max_tokens: int = 800,
    keep_last: int = 4,
) -> list[dict[str, str]]:
    """Keep recent turns; replace older turns with a short extractive summary."""
    if not history:
        return []
    if count_tokens(_serialize(history)) <= max_tokens:
        return list(history)

    keep_last = max(1, keep_last)
    if len(history) <= keep_last:
        return list(history)

    older = history[:-keep_last]
    recent = history[-keep_last:]
    bullets = []
    for msg in older:
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip().replace("\n", " ")
        if not content:
            continue
        bullets.append(f"- {role}: {content[:200]}")
    summary = {
        "role": "user",
        "content": "Prior conversation summary:\n" + "\n".join(bullets[:40]),
    }
    candidate = [summary, *recent]
    if count_tokens(_serialize(candidate)) < count_tokens(_serialize(history)):
        # Prefer cheaper serialization; apply_if_cheaper works on strings — map back.
        cheaper = apply_if_cheaper(_serialize(history), _serialize(candidate))
        if cheaper == _serialize(candidate):
            return candidate
    return recent
