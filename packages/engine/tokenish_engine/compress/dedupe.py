"""Lossless near-duplicate section removal for repeated PAGE BREAK / paste blocks."""

from __future__ import annotations

import hashlib
import re

from tokenish_engine.meters.tokens import count_tokens


def _fingerprint(section: str) -> str:
    norm = re.sub(r"\s+", " ", (section or "").strip().lower())
    if len(norm) < 40:
        return ""
    # Stable hash of normalized body (ignore tiny whitespace differences)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def dedupe_document_sections(text: str) -> tuple[str, int, str]:
    """
    Drop repeated sections (exact/near-exact after whitespace normalize).
    Returns (text, dropped_count, joiner_hint_stage).
    Safe for assess/analyze; also safe in follow-mode for true duplicates.
    """
    if not text or count_tokens(text) < 400:
        return text, 0, ""

    if "--- PAGE BREAK ---" in text:
        parts = [p.strip() for p in text.split("--- PAGE BREAK ---")]
        joiner = "\n--- PAGE BREAK ---\n"
    else:
        parts = [p.strip() for p in re.split(r"\n{2,}", text)]
        joiner = "\n\n"

    parts = [p for p in parts if p]
    if len(parts) <= 1:
        # Also try line-block dedupe for consecutive identical blocks
        return text, 0, ""

    kept: list[str] = []
    seen: set[str] = set()
    dropped = 0
    for part in parts:
        fp = _fingerprint(part)
        if not fp:
            kept.append(part)
            continue
        if fp in seen:
            dropped += 1
            continue
        seen.add(fp)
        kept.append(part)

    if dropped <= 0:
        return text, 0, ""

    out = joiner.join(kept)
    if count_tokens(out) >= count_tokens(text):
        return text, 0, ""
    return out, dropped, f"dedupe_drop_{dropped}"
