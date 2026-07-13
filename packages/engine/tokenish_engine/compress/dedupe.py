"""Near-duplicate section removal for repeated PAGE BREAK / PDF paste blocks."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher

from tokenish_engine.meters.tokens import count_tokens

_PAGE_NUM = re.compile(
    r"(?i)\b(page|pg\.?)\s*\d+\b|\b\d+\s*/\s*\d+\b|^\s*\d+\s*$",
    re.MULTILINE,
)


def _normalize(section: str) -> str:
    text = (section or "").replace("\f", "\n")
    text = _PAGE_NUM.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _fingerprint(section: str) -> str:
    norm = _normalize(section)
    if len(norm) < 40:
        return ""
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def _is_near_duplicate(a: str, b: str, *, threshold: float = 0.85) -> bool:
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # Shared long prefix (repeated prompt templates with tiny tails)
    n = min(len(na), len(nb), 800)
    if n >= 100 and na[:n] == nb[:n]:
        return True
    # Compare cores (strip short header/footer noise)
    def core(s: str) -> str:
        if len(s) < 200:
            return s
        cut = max(40, len(s) // 10)
        return s[cut:-cut]

    ca, cb = core(na), core(nb)
    if ca and cb and ca == cb:
        return True
    ratio = SequenceMatcher(None, na[:3000], nb[:3000]).ratio()
    if ratio >= threshold:
        return True
    return SequenceMatcher(None, ca[:3000], cb[:3000]).ratio() >= threshold


def _split_sections(text: str) -> tuple[list[str], str]:
    raw = text.replace("\f", "\n--- PAGE BREAK ---\n")
    if "--- PAGE BREAK ---" in raw:
        parts = [p.strip() for p in raw.split("--- PAGE BREAK ---")]
        return [p for p in parts if p], "\n--- PAGE BREAK ---\n"
    # Prefer large paragraph blocks for fuzzy compare
    parts = [p.strip() for p in re.split(r"\n{2,}", raw)]
    return [p for p in parts if p], "\n\n"


def dedupe_document_sections(text: str) -> tuple[str, int, str]:
    """
    Drop repeated / near-duplicate sections after whitespace + page-number normalize.
    Returns (text, dropped_count, stage_name).
    """
    if not text or count_tokens(text) < 400:
        return text, 0, ""

    parts, joiner = _split_sections(text)
    if len(parts) <= 1:
        return text, 0, ""

    kept: list[str] = []
    dropped = 0
    for part in parts:
        fp = _fingerprint(part)
        dup = False
        if fp and any(_fingerprint(k) == fp for k in kept):
            dup = True
        elif any(_is_near_duplicate(part, k) for k in kept):
            dup = True
        if dup:
            dropped += 1
            continue
        kept.append(part)

    if dropped <= 0 or not kept:
        return text, 0, ""

    out = joiner.join(kept)
    if count_tokens(out) >= count_tokens(text):
        return text, 0, ""
    return out, dropped, f"dedupe_drop_{dropped}"
