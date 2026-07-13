"""Mumblz title agent tests."""

from tokenish_engine.agents import mumblz_name_thread, mumblz_title, strip_vowels_word


def test_mumblz_strips_vowels():
    assert strip_vowels_word("Combinatorics") == "Cmbntrcs"
    assert strip_vowels_word("Critique") == "Crtq"
    assert mumblz_title("Neon Cityscape Review") == "Nn Ctyscp Rvw"


def test_mumblz_unicombinatorics_title():
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
    joined = " ".join(parts).lower()
    assert "a" not in joined and "e" not in joined and "i" not in joined
    assert "o" not in joined and "u" not in joined


def test_mumblz_three_words():
    msgs = [
        {"role": "user", "content": "Deeply Assess the attached. I want color and details of ratios and styles."},
        {
            "role": "assistant",
            "content": "Neon parking booth night cityscape with painterly blues and warm accents.",
        },
    ]
    title = mumblz_name_thread(msgs)
    assert len(title.split()) == 3
