from __future__ import annotations

import json

from tokenish_engine.compile.format_rewrite import maybe_tabular_cheaper
from tokenish_engine.meters.tokens import count_tokens


def test_list_of_dicts_becomes_csv_when_cheaper():
    rows = [{"name": "John Smith", "age": 34, "city": "Toronto"} for _ in range(20)]
    raw = json.dumps(rows)
    out, applied = maybe_tabular_cheaper(raw)
    assert applied is True
    assert count_tokens(out) < count_tokens(raw)
    assert "John Smith" in out


def test_nested_json_left_alone():
    raw = json.dumps({"a": {"b": [1, {"c": 2}]}})
    out, applied = maybe_tabular_cheaper(raw)
    assert applied is False
    assert out == raw
