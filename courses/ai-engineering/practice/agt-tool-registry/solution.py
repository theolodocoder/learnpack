import inspect
import re
import typing
from typing import Literal

TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


def _json_type(name: str, hint) -> dict:
    if typing.get_origin(hint) is Literal:
        return {"type": "string", "enum": list(typing.get_args(hint))}
    if hint in TYPES:
        return {"type": TYPES[hint]}
    raise TypeError(f"parameter {name!r}: unsupported type {hint!r}")


def _arg_docs(doc: str) -> dict[str, str]:
    """Read 'name: description' lines from a Google-style Args: section."""
    _, sep, rest = doc.partition("Args:")
    if not sep:
        return {}
    out = {}
    for line in rest.splitlines():
        if line.strip() and not line.startswith((" ", "\t")):
            break  # a new unindented section ends Args
        m = re.match(r"\s*(\w+)\s*:\s*(.+)", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


class ToolRegistry:
    def __init__(self):
        self._tools = {}  # name -> (function, schema)

    def tool(self, fn):
        """Decorator: build fn's tool schema, register it, and return fn unchanged."""
        hints = typing.get_type_hints(fn)
        doc = inspect.getdoc(fn) or ""
        arg_docs = _arg_docs(doc)
        properties, required = {}, []
        for name, param in inspect.signature(fn).parameters.items():
            if name not in hints:
                raise TypeError(f"parameter {name!r} of {fn.__name__} needs a type hint")
            prop = _json_type(name, hints[name])
            if name in arg_docs:
                prop["description"] = arg_docs[name]
            properties[name] = prop
            if param.default is inspect.Parameter.empty:
                required.append(name)
        schema = {
            "name": fn.__name__,
            "description": doc.split("\n\n")[0].strip(),
            "input_schema": {"type": "object", "properties": properties,
                             "required": required, "additionalProperties": False},
        }
        self._tools[fn.__name__] = (fn, schema)
        return fn

    def schemas(self) -> list[dict]:
        return [schema for _, schema in self._tools.values()]

    def call(self, name: str, input: dict) -> str:
        fn, _ = self._tools[name]
        return str(fn(**input))
