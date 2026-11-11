import json
from pathlib import Path


class ConfigError(Exception):
    """Raised when the config file is missing or invalid."""


def load_config(path: str | Path) -> dict:
    """Read a JSON config file, check it, and fill in defaults."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ConfigError(f"{path} is not valid JSON: {err}") from err
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    if "model" not in data:
        raise ConfigError(f"{path} is missing the 'model' key")
    data.setdefault("max_tokens", 1024)
    return data


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "config.json"
        p.write_text('{"model": "claude-haiku-5-5"}')
        try:
            print(load_config(p))
            print(load_config(Path(d) / "missing.json"))
        except ConfigError as e:
            print("ConfigError:", e)
