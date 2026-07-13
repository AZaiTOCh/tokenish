"""Mumblz title agent tests."""

from tokenish_engine.agents import mumblz_name_thread, mumblz_title, strip_vowels_word
from tokenish_engine.agents.mumblz import mumble_clarity


def test_mumblz_strips_vowels():
    assert strip_vowels_word("Combinatorics") == "Cmbntrcs"
    assert strip_vowels_word("Critique") == "Crtq"
    assert mumblz_title("Neon Cityscape Review") == "Nn Ctyscp Rvw"


def test_clarity_prefers_consonant_rich_words():
    assert mumble_clarity("Combinatorics") > mumble_clarity("Neon")
    assert mumble_clarity("Critique") > mumble_clarity("Brief")
    assert mumble_clarity("Benchmark") > mumble_clarity("Idea")


def test_mumblz_avoids_unreadable_stubs():
    msgs = [
        {
            "role": "user",
            "content": (
                "Deeply Assess the attached. Then check its validity with trusted online "
                "sources. Then generate a one page exec summary. Then act as adversarial "
                "peer reviewer. Unicombinatorics freefactorial G-Triangle."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "The Freefactorial framework and Unicombinatorics claims overlap known "
                "partial permutation sums. Peer review finds nomenclature inflation."
            ),
        },
    ]
    title = mumblz_name_thread(msgs)
    parts = title.split()
    assert len(parts) == 3
    # Every mumbled word should keep a usable consonant frame
    assert all(len(p) >= 3 for p in parts)
    joined = " ".join(parts).lower()
    assert "a" not in joined and "e" not in joined and "i" not in joined
    assert "o" not in joined and "u" not in joined
    # Should not collapse to tiny stubs like Nn / Brf
    assert "Nn" not in parts and "Brf" not in parts


def test_mumblz_three_words_palette_chat():
    msgs = [
        {"role": "user", "content": "Deeply Assess the attached. I want color and details of ratios and styles."},
        {
            "role": "assistant",
            "content": "Neon parking booth night cityscape with painterly blues and warm accents.",
        },
    ]
    title = mumblz_name_thread(msgs)
    parts = title.split()
    assert len(parts) == 3
    assert all(len(p) >= 3 for p in parts)
