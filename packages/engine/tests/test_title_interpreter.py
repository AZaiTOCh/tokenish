"""Title interpreter unit tests."""

from tokenish_engine.agents import interpret_thread_title, normalize_three_word_title


def test_three_word_unicombinatorics_title():
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
    title = interpret_thread_title(msgs)
    parts = title.split()
    assert len(parts) == 3
    assert any(p.lower() in {"combinatorics", "critique", "vetting", "brief", "audit", "math"} for p in parts)


def test_three_word_palette_title():
    msgs = [
        {"role": "user", "content": "Deeply Assess the attached. I want color and details of ratios and styles."},
        {
            "role": "assistant",
            "content": "Neon parking booth night cityscape with painterly blues and warm accents.",
        },
    ]
    title = interpret_thread_title(msgs)
    assert len(title.split()) == 3


def test_normalize_three_words():
    assert normalize_three_word_title('"Neon City Review"') == "Neon City Review"
    assert len(normalize_three_word_title("onlytwo").split()) == 3
