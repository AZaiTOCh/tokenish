from __future__ import annotations

import csv
import io
import json

from tokenish_engine.compile.tokenizer_gate import apply_if_cheaper


def maybe_tabular_cheaper(text: str) -> tuple[str, bool]:
    """Rewrite a flat list-of-dicts JSON array to CSV when it is cheaper."""
    stripped = (text or "").strip()
    if not stripped.startswith("["):
        return text, False
    try:
        data = json.loads(stripped)
    except Exception:
        return text, False
    if not isinstance(data, list) or not data or not all(isinstance(x, dict) for x in data):
        return text, False
    keys = list(data[0].keys())
    if not keys or any(set(x.keys()) != set(keys) for x in data):
        return text, False
    if any(isinstance(v, (dict, list)) for row in data for v in row.values()):
        return text, False
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    writer.writeheader()
    writer.writerows(data)
    csv_text = buf.getvalue()
    cheaper = apply_if_cheaper(text, csv_text)
    return cheaper, cheaper != text
