# Load a config file safely

AI apps usually read settings (model name, token limits, prompts) from a JSON file. When that file is missing or broken, the program should fail with one clear error type, not a random `KeyError` deep inside.

Write a custom exception and a loader:

```python
class ConfigError(Exception): ...

def load_config(path: str | Path) -> dict:
```

`load_config` must:

1. Accept a `str` or a `pathlib.Path`.
2. Raise `ConfigError` if the file does not exist.
3. Raise `ConfigError` if the file is not valid JSON, or if the JSON is not an object (a dict).
4. Raise `ConfigError` if the `"model"` key is missing.
5. Fill in `"max_tokens": 1024` when that key is missing (keep the file's value if present).
6. Return the dict.

Put a helpful message in each `ConfigError`, and use `raise ConfigError(...) from err` when you convert another exception.

Example: a file `config.json` containing `{"model": "claude-haiku-5-5"}` gives

```python
load_config("config.json")
# {'model': 'claude-haiku-5-5', 'max_tokens': 1024}
```
