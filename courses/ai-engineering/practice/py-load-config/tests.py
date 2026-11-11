import tempfile
from pathlib import Path

from solution import ConfigError, load_config


def _write(text: str) -> Path:
    d = Path(tempfile.mkdtemp())
    p = d / "config.json"
    p.write_text(text)
    return p


def _raises_config_error(path) -> bool:
    try:
        load_config(path)
    except ConfigError:
        return True
    return False


def test_loads_file_and_adds_default_max_tokens():
    got = load_config(_write('{"model": "claude-haiku-5-5"}'))
    want = {"model": "claude-haiku-5-5", "max_tokens": 1024}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_keeps_max_tokens_from_file_and_accepts_str_path():
    got = load_config(str(_write('{"model": "m", "max_tokens": 50}')))
    want = {"model": "m", "max_tokens": 50}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_missing_file_raises_config_error():
    missing = Path(tempfile.mkdtemp()) / "nope.json"
    assert _raises_config_error(missing), "a missing file should raise ConfigError"


def test_invalid_json_raises_config_error():
    assert _raises_config_error(_write("{not json")), "invalid JSON should raise ConfigError"


def test_non_object_json_raises_config_error():
    assert _raises_config_error(_write("[1, 2, 3]")), "a JSON list should raise ConfigError"


def test_missing_model_raises_config_error():
    assert _raises_config_error(_write('{"max_tokens": 10}')), "a config without 'model' should raise ConfigError"
