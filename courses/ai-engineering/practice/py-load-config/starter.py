import json
from pathlib import Path


class ConfigError(Exception):
    """Raised when the config file is missing or invalid."""


def load_config(path: str | Path) -> dict:
    """Read a JSON config file, check it, and fill in defaults."""
    path = Path(path)
    # TODO: raise ConfigError if the file doesn't exist (path.exists())
    # TODO: parse path.read_text() with json.loads; turn json.JSONDecodeError into ConfigError
    # TODO: raise ConfigError if the result isn't a dict or has no "model" key
    # TODO: default max_tokens to 1024, then return the dict
    raise NotImplementedError


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
        except NotImplementedError:
            print("Not implemented yet: fill in the TODOs, then Run again.")
