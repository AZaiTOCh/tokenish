from __future__ import annotations

import json
import os
from pathlib import Path


def tokenish_home() -> Path:
    raw = os.environ.get("TOKENISH_HOME")
    if raw:
        return Path(raw)
    return Path.home() / ".tokenish"


def config_path() -> Path:
    return tokenish_home() / "config.json"


def load_keys() -> dict[str, str]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {k: str(v) for k, v in (data.get("keys") or {}).items() if v}


def save_keys(keys: dict[str, str]) -> Path:
    home = tokenish_home()
    home.mkdir(parents=True, exist_ok=True)
    path = config_path()
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    merged = dict(existing.get("keys") or {})
    for key, value in keys.items():
        if value:
            merged[key] = value
    existing["keys"] = merged
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return path


def apply_saved_keys_to_environ() -> dict[str, str]:
    """Load ~/.tokenish keys into os.environ when not already set."""
    loaded = load_keys()
    for key, value in loaded.items():
        os.environ.setdefault(key, value)
    return loaded
