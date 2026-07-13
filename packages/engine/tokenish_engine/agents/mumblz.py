"""
Mumblz — History title agent.

Reads a full dialog, picks three words that stay clearest after vowel removal,
then applies the Mumblz mumble (strip vowels) for the History label.
"""

from __future__ import annotations

import re
from collections import Counter

_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "that", "this",
    "these", "those", "to", "of", "in", "on", "for", "with", "as", "by", "at",
    "from", "into", "about", "over", "after", "before", "between", "is", "are",
    "was", "were", "be", "been", "being", "it", "its", "i", "you", "we", "they",
    "he", "she", "my", "your", "our", "their", "me", "him", "her", "them",
    "do", "does", "did", "doing", "done", "have", "has", "had", "having",
    "will", "would", "can", "could", "should", "may", "might", "must", "not",
    "no", "yes", "so", "very", "just", "also", "only", "more", "most", "some",
    "any", "all", "each", "every", "both", "few", "other", "such", "own",
    "same", "too", "out", "up", "down", "off", "again", "further", "once",
    "here", "there", "when", "where", "why", "how", "what", "which", "who",
    "whom", "whose", "please", "thanks", "thank", "attached", "attachment",
    "document", "documents", "file", "files", "pdf", "image", "images", "new",
    "want", "need", "make", "get", "like", "using", "used", "use", "based",
    "following", "below", "above", "one", "two", "three", "first", "second",
    "final", "generate", "generated", "provide", "provided", "deeply", "whole",
    "check", "checked", "online", "sources", "source", "trusted", "relevant",
    "everything", "something", "anything", "page", "pages", "part", "parts",
    "color", "colour", "colors", "colours",  # prefer Palette / Chromatic
    "brief", "neon",  # mumble poorly (Brf / Nn) — prefer clearer aliases
}

# Labels chosen because consonant skeletons stay readable (Cmbntrcs, Bnchmrk, …)
_TOPIC_MAP: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"unicombinator|freefactorial|freesar|superfreefactorial|g[- ]?triangle", re.I), "Combinatorics", 12),
    (re.compile(r"\bgveb\b|waldo|raphael|bosch|visual exhaustion|grounded visual", re.I), "Benchmark", 12),
    (re.compile(r"palette|color|colours?|chiaroscuro|brushstroke|painterly|chromatic", re.I), "Chromatic", 10),
    (re.compile(r"quantum|cryptograph|shor|grover", re.I), "Quantum", 9),
    (re.compile(r"peer review|adversar|critique|auditor", re.I), "Critique", 9),
    (re.compile(r"exec(utive)?\s*summary|one[- ]?page|brief", re.I), "Digest", 8),
    (re.compile(r"fact[- ]?check|vetting|validity|verify|verification", re.I), "Vetting", 8),
    (re.compile(r"token|tokex|multimodal|llm|benchmark", re.I), "Tokens", 7),
    (re.compile(r"urban|street|parking|dusk|cityscape|nocturne", re.I), "Cityscape", 8),
    (re.compile(r"animation|cel[- ]?shad|cartoon|character", re.I), "Animation", 8),
    (re.compile(r"mathematic|formula|permutation|factorial|subset", re.I), "Mathcraft", 7),
    (re.compile(r"synthesis|integrat", re.I), "Synthesis", 6),
    (re.compile(r"assess|analysis|analyze|analyse", re.I), "Assessment", 5),
]

_TASK_MAP: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"adversar|peer review|critique", re.I), "Critique", 10),
    (re.compile(r"fact[- ]?check|vet|valid", re.I), "Audit", 9),
    (re.compile(r"summar|brief|exec", re.I), "Digest", 8),
    (re.compile(r"break\s*down|ratio|style|pattern|color", re.I), "Breakdown", 8),
    (re.compile(r"synthes", re.I), "Synthesis", 7),
    (re.compile(r"assess|analy", re.I), "Scrutiny", 6),
    (re.compile(r"compare|contrast", re.I), "Contrast", 6),
]

# Prefer these when semantics collide — strong consonant frames
_MUMBLE_FRIENDLY_DEFAULTS = [
    "Scrutiny", "Digest", "Breakdown", "Synthesis", "Contrast",
    "Framework", "Signalcraft", "Threadmark", "Spotlight", "Blueprint",
]

_STYLE_WORDS = {
    "urban", "cinematic", "painterly", "quantum", "visual", "grounded",
    "combinatorial", "adversarial", "executive", "academic", "critical",
    "spectral", "nocturne", "chrome", "verdant", "crimson", "chromatic",
    "framework", "benchmark", "cityscape", "animation",
}

_VOWELS = set("aeiouAEIOU")


def strip_vowels_word(word: str) -> str:
    """Mumblz mumble: drop vowels; keep at least one character."""
    if not word:
        return word
    parts = word.split("-") if "-" in word else [word]
    out: list[str] = []
    for part in parts:
        core = "".join(c for c in part if c not in _VOWELS)
        if not core:
            core = part[:1]
        out.append(core[0].upper() + core[1:] if core else core)
    return "-".join(out)


def mumblz_title(title: str) -> str:
    """Apply vowel stripping to each word of a 3-word title."""
    parts = [p for p in re.split(r"\s+", (title or "").strip()) if p]
    if not parts:
        return "Frsh Tkn Thrd"
    return " ".join(strip_vowels_word(p) for p in parts[:3])


def mumble_clarity(word: str) -> float:
    """
    How readable is this word after vowel removal?
    Mumblz prefers long, varied consonant skeletons (Cmbntrcs) over stubs (Nn, Brf).
    """
    raw = re.sub(r"[^A-Za-z0-9-]", "", word or "")
    if not raw:
        return 0.0
    stub = strip_vowels_word(raw)
    n = len(stub.replace("-", ""))
    if n <= 1:
        return 0.05
    if n == 2:
        return 0.35
    if n == 3:
        score = 1.1
    else:
        score = 1.4 + (n - 3) * 0.55
    # Distinct consonant letters help recognition
    score += len(set(stub.lower().replace("-", ""))) * 0.35
    # Prefer stub that still starts like the original word
    if stub and raw and stub[0].lower() == raw[0].lower():
        score += 0.6
    # Soft penalty for very vowel-heavy originals that collapse hard
    vowel_ratio = sum(1 for c in raw if c in _VOWELS) / max(1, len(raw))
    if vowel_ratio > 0.45:
        score *= 0.75
    return score


def _title_case(word: str) -> str:
    if not word:
        return word
    if word.isupper() and len(word) <= 4:
        return word
    return word[:1].upper() + word[1:].lower()


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9'-]{2,}", text or "")


def _dialog_blob(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for m in messages or []:
        role = (m.get("role") or "").lower()
        content = (m.get("content") or "").strip()
        if not content or content.startswith("Attach a pdf"):
            continue
        if role in {"user", "assistant"}:
            parts.append(content[:1200] if role == "user" else content[:800])
    return "\n".join(parts)


def _pick_topics(blob: str) -> list[tuple[str, float]]:
    hits: list[tuple[str, float]] = []
    seen: set[str] = set()
    for pat, label, score in _TOPIC_MAP:
        if pat.search(blob) and label.lower() not in seen:
            hits.append((label, float(score)))
            seen.add(label.lower())
    return hits


def _pick_tasks(blob: str) -> list[tuple[str, float]]:
    hits: list[tuple[str, float]] = []
    seen: set[str] = set()
    for pat, label, score in _TASK_MAP:
        if pat.search(blob) and label.lower() not in seen:
            hits.append((label, float(score)))
            seen.add(label.lower())
    return hits


def _keyword_pool(blob: str) -> list[tuple[str, float]]:
    counts: Counter[str] = Counter()
    for w in _words(blob):
        low = w.lower()
        if low in _STOP or len(low) < 4:
            continue
        weight = 2 if low in _STYLE_WORDS else 1
        counts[low] += weight
    return [(w, float(n) + 2.0) for w, n in counts.most_common(40)]


def _candidate_pool(blob: str) -> list[tuple[str, float]]:
    """(clear_word, semantic_score) — Mumblz will re-rank by mumble clarity."""
    pool: dict[str, float] = {}

    def add(word: str, sem: float) -> None:
        tw = _title_case(re.sub(r"[^A-Za-z0-9-]", "", word))
        if not tw or tw.lower() in _STOP:
            return
        if mumble_clarity(tw) < 0.9:  # reject unreadable stubs early
            return
        pool[tw] = max(pool.get(tw, 0.0), sem)

    for label, sem in _pick_topics(blob):
        add(label, sem + 8)
    for label, sem in _pick_tasks(blob):
        add(label, sem + 7)
    for word, sem in _keyword_pool(blob):
        add(word, sem)
    for i, word in enumerate(_MUMBLE_FRIENDLY_DEFAULTS):
        add(word, 3.5 - i * 0.15)
    return list(pool.items())


def _rank_for_mumble(candidates: list[tuple[str, float]]) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for word, sem in candidates:
        clarity = mumble_clarity(word)
        # Clarity matters, but dialog-matched topics/tasks still win.
        total = clarity * 1.55 + sem * 1.15
        ranked.append((word, total))
    ranked.sort(key=lambda x: -x[1])
    return ranked


def _three_word_clear(messages: list[dict[str, str]]) -> str:
    """Pick three clear words optimized for post-mumble readability."""
    blob = _dialog_blob(messages)
    if not blob.strip():
        return "Fresh Token Thread"

    ranked = _rank_for_mumble(_candidate_pool(blob))
    picked: list[str] = []
    used_stubs: set[str] = set()

    for word, _score in ranked:
        stub = strip_vowels_word(word).lower()
        if stub in used_stubs:
            continue
        if word.lower() in {w.lower() for w in picked}:
            continue
        # Skip near-duplicate stubs (Frsh / Frshx)
        if any(stub.startswith(u[:3]) and u.startswith(stub[:3]) for u in used_stubs if len(u) >= 3):
            continue
        picked.append(word)
        used_stubs.add(stub)
        if len(picked) >= 3:
            break

    while len(picked) < 3:
        for fallback in _MUMBLE_FRIENDLY_DEFAULTS:
            if fallback.lower() not in {w.lower() for w in picked}:
                picked.append(fallback)
                break
        else:
            picked.append(["Signalcraft", "Blueprint", "Threadmark"][len(picked) % 3])

    return " ".join(picked[:3])


def normalize_three_word_title(raw: str, fallback: str = "Fresh Token Thread") -> str:
    cleaned = re.sub(r"[\"'`#*_]+", "", (raw or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.split("\n", 1)[0].strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    if len(parts) >= 3:
        # Re-pick among LLM words by mumble clarity when possible
        ranked = _rank_for_mumble([(_title_case(p), 5.0) for p in parts[:8]])
        clear = " ".join(w for w, _ in ranked[:3])
        if len(clear.split()) < 3:
            clear = " ".join(_title_case(p) for p in parts[:3])
    elif len(parts) == 2:
        clear = f"{_title_case(parts[0])} {_title_case(parts[1])} Digest"
    elif len(parts) == 1:
        clear = f"{_title_case(parts[0])} Token Digest"
    else:
        clear = fallback
    return mumblz_title(clear)


def mumblz_name_thread(messages: list[dict[str, str]]) -> str:
    """Mumblz: dialog → clarity-aware 3-word title → vowel-stripped label."""
    return mumblz_title(_three_word_clear(messages))


interpret_thread_title = mumblz_name_thread


async def mumblz_name_thread_llm(messages: list[dict[str, str]]) -> str | None:
    """Optional LLM polish with Mumblz clarity constraint, then vowel strip."""
    local_clear = _three_word_clear(messages)
    blob = _dialog_blob(messages)
    if len(blob) < 40:
        return mumblz_title(local_clear)
    prompt = (
        "Read this chat and reply with ONLY three Title Case words for a history title.\n"
        "CRITICAL: choose words that stay readable AFTER all vowels (a,e,i,o,u) are removed.\n"
        "Prefer long consonant-rich words (Combinatorics→Cmbntrcs, Critique→Crtq, Benchmark→Bnchmrk).\n"
        "Avoid short vowel-heavy words (Neon, Brief, Color, Idea).\n"
        "No quotes, punctuation, or explanation.\n\n"
        f"CHAT:\n{blob[:3500]}\n\n"
        f"Local Mumblz draft (improve if needed): {local_clear}"
    )
    try:
        from tokenish_engine.dispatch import chat_complete, resolve_model, resolve_provider

        provider = resolve_provider("auto", None, "gemini-3.5-flash")
        model = resolve_model(provider, None, "gemini-3.5-flash")
        text = await chat_complete(
            provider=provider,
            model=model,
            envelope=prompt,
            history=[],
        )
        return normalize_three_word_title(text, fallback=local_clear)
    except Exception:
        return None


interpret_thread_title_llm = mumblz_name_thread_llm
