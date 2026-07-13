"""
Mumblz — History title agent.

Reads a full dialog, invents a crisp 3-word title, then strips vowels
(Mumblz "mumble") for the History label.
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
}

_TOPIC_MAP: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"unicombinator|freefactorial|freesar|superfreefactorial|g[- ]?triangle", re.I), "Combinatorics", 12),
    (re.compile(r"\bgveb\b|waldo|raphael|bosch|visual exhaustion|grounded visual", re.I), "Benchmark", 12),
    (re.compile(r"palette|color|colours?|chiaroscuro|brushstroke|painterly|neon", re.I), "Palette", 10),
    (re.compile(r"quantum|cryptograph|shor|grover", re.I), "Quantum", 9),
    (re.compile(r"peer review|adversar|critique|auditor", re.I), "Critique", 9),
    (re.compile(r"exec(utive)?\s*summary|one[- ]?page|brief", re.I), "Brief", 8),
    (re.compile(r"fact[- ]?check|vetting|validity|verify|verification", re.I), "Vetting", 8),
    (re.compile(r"token|tokex|multimodal|llm|benchmark", re.I), "Tokens", 7),
    (re.compile(r"urban|street|parking|dusk|cityscape", re.I), "Cityscape", 8),
    (re.compile(r"animation|cel[- ]?shad|cartoon|character", re.I), "Animation", 8),
    (re.compile(r"mathematic|formula|permutation|factorial|subset", re.I), "Math", 7),
    (re.compile(r"synthesis|integrat", re.I), "Synthesis", 6),
    (re.compile(r"assess|analysis|analyze|analyse", re.I), "Assessment", 5),
]

_TASK_MAP: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r"adversar|peer review|critique", re.I), "Critique", 10),
    (re.compile(r"fact[- ]?check|vet|valid", re.I), "Audit", 9),
    (re.compile(r"summar|brief|exec", re.I), "Brief", 8),
    (re.compile(r"break\s*down|ratio|style|pattern|color", re.I), "Breakdown", 8),
    (re.compile(r"synthes", re.I), "Synthesis", 7),
    (re.compile(r"assess|analy", re.I), "Review", 6),
    (re.compile(r"compare|contrast", re.I), "Compare", 6),
]

_STYLE_WORDS = {
    "neon", "urban", "cinematic", "painterly", "quantum", "visual", "grounded",
    "combinatorial", "adversarial", "executive", "academic", "critical",
    "spectral", "nocturne", "chrome", "verdant", "crimson", "azure", "amber",
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


def _pick_topics(blob: str) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    seen: set[str] = set()
    for pat, label, score in _TOPIC_MAP:
        if pat.search(blob) and label.lower() not in seen:
            hits.append((label, score))
            seen.add(label.lower())
    return sorted(hits, key=lambda x: -x[1])


def _pick_tasks(blob: str) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    seen: set[str] = set()
    for pat, label, score in _TASK_MAP:
        if pat.search(blob) and label.lower() not in seen:
            hits.append((label, score))
            seen.add(label.lower())
    return sorted(hits, key=lambda x: -x[1])


def _keyword_pool(blob: str) -> list[str]:
    counts: Counter[str] = Counter()
    for w in _words(blob):
        low = w.lower()
        if low in _STOP or len(low) < 4:
            continue
        weight = 2 if low in _STYLE_WORDS else 1
        counts[low] += weight
    return [w for w, _n in counts.most_common(24)]


def _three_word_clear(messages: list[dict[str, str]]) -> str:
    """Clear (voweled) three-word title before Mumblz mumble."""
    blob = _dialog_blob(messages)
    if not blob.strip():
        return "Fresh Token Thread"

    topics = _pick_topics(blob)
    tasks = _pick_tasks(blob)
    keys = _keyword_pool(blob)
    words: list[str] = []

    def push(w: str) -> None:
        tw = _title_case(re.sub(r"[^A-Za-z0-9-]", "", w))
        if not tw or tw.lower() in {x.lower() for x in words}:
            return
        if tw.lower() in _STOP:
            return
        words.append(tw)

    if topics:
        push(topics[0][0])
    if keys:
        for k in keys:
            if k.lower() not in {w.lower() for w in words} and k.lower() not in {
                t[0].lower() for t in topics
            }:
                push(k)
                break
    if tasks:
        push(tasks[0][0])
    elif topics and len(topics) > 1:
        push(topics[1][0])

    defaults = ["Insight", "Session", "Thread", "Study", "Focus", "Signal"]
    for k in keys + defaults:
        if len(words) >= 3:
            break
        push(k)

    while len(words) < 3:
        words.append(["Alpha", "Signal", "Thread"][len(words)])

    return " ".join(words[:3])


def normalize_three_word_title(raw: str, fallback: str = "Fresh Token Thread") -> str:
    cleaned = re.sub(r"[\"'`#*_]+", "", (raw or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.split("\n", 1)[0].strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    if len(parts) >= 3:
        clear = " ".join(_title_case(p) for p in parts[:3])
    elif len(parts) == 2:
        clear = f"{_title_case(parts[0])} {_title_case(parts[1])} Study"
    elif len(parts) == 1:
        clear = f"{_title_case(parts[0])} Token Thread"
    else:
        clear = fallback
    return mumblz_title(clear)


def mumblz_name_thread(messages: list[dict[str, str]]) -> str:
    """Mumblz: dialog → 3-word title → vowel-stripped History label."""
    return mumblz_title(_three_word_clear(messages))


# Back-compat aliases
interpret_thread_title = mumblz_name_thread


async def mumblz_name_thread_llm(messages: list[dict[str, str]]) -> str | None:
    """Optional LLM polish, then Mumblz vowel strip. None on failure."""
    local_clear = _three_word_clear(messages)
    blob = _dialog_blob(messages)
    if len(blob) < 40:
        return mumblz_title(local_clear)
    prompt = (
        "Read this chat and reply with ONLY three words: a punchy Title Case "
        "history title (no quotes, no punctuation, no explanation).\n\n"
        f"CHAT:\n{blob[:3500]}\n\n"
        f"Local draft (improve if needed): {local_clear}"
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
