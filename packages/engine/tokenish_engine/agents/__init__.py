"""Mumblz — History title agent (3-word titles, then vowel-stripped)."""

from tokenish_engine.agents.mumblz import (
    interpret_thread_title,
    interpret_thread_title_llm,
    mumblz_name_thread,
    mumblz_name_thread_llm,
    mumblz_title,
    normalize_three_word_title,
    strip_vowels_word,
)

__all__ = [
    "mumblz_name_thread",
    "mumblz_name_thread_llm",
    "mumblz_title",
    "strip_vowels_word",
    "normalize_three_word_title",
    "interpret_thread_title",
    "interpret_thread_title_llm",
]
