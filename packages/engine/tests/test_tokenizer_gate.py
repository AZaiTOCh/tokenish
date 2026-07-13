from __future__ import annotations

from tokenish_engine.compile.tokenizer_gate import apply_if_cheaper, reject_char_shorthand
from tokenish_engine.meters.tokens import count_tokens


def test_vowel_shorthand_increases_tokens_and_is_rejected():
    original = "Build a token optimization framework that saves tokens"
    bad = "Bld a tkn optmztn frmwrk tht svs tkns"
    assert count_tokens(bad) >= count_tokens(original)
    assert reject_char_shorthand(bad) is True


def test_normal_english_not_rejected():
    text = "Please review the attached document and let me know if you have any questions."
    assert reject_char_shorthand(text) is False


def test_filler_deletion_is_kept_when_cheaper():
    original = "Please could you kindly help me summarize the key points"
    cleaned = "Summarize the key points"
    out = apply_if_cheaper(original, cleaned)
    assert out == cleaned
    assert count_tokens(out) < count_tokens(original)


def test_apply_if_cheaper_keeps_original_on_tie_or_worse():
    text = "hello world"
    assert apply_if_cheaper(text, text) == text
    assert apply_if_cheaper(text, text + " !!!") == text
