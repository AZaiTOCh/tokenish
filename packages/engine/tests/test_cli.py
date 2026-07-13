from __future__ import annotations

from tokenish_engine.cli import build_parser, main
from tokenish_engine.settings_store import load_keys, save_keys


def test_parser_has_serve_doctor_version():
    parser = build_parser()
    assert parser.parse_args(["version"]).cmd == "version"
    assert parser.parse_args(["doctor"]).cmd == "doctor"
    assert parser.parse_args(["serve"]).cmd == "serve"


def test_main_version(capsys):
    assert main(["version"]) == 0
    assert "0.2.0" in capsys.readouterr().out


def test_save_and_load_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKENISH_HOME", str(tmp_path))
    save_keys({"GPT_TOKENISH": "sk-test", "GEMINI_API_KEY": "gem-test"})
    data = load_keys()
    assert data["GPT_TOKENISH"] == "sk-test"
    assert data["GEMINI_API_KEY"] == "gem-test"
    assert (tmp_path / "config.json").exists()
