from __future__ import annotations

from tokenish_engine.history.summarize import compress_history
from tokenish_engine.meters.tokens import count_tokens


def test_long_history_is_shortened():
    hist = [{"role": "user", "content": "x" * 500}, {"role": "assistant", "content": "y" * 500}] * 6
    out = compress_history(hist, max_tokens=800)
    joined = "\n".join(m["content"] for m in out)
    assert count_tokens(joined) <= 900
    assert out[-1]["role"] in {"user", "assistant"}
