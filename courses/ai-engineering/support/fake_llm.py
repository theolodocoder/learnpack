"""A fake Claude client for offline, free, repeatable exercise tests.

It mimics the parts of `anthropic.Anthropic()` the course uses:
  client.messages.create(...)   -> response with .content, .stop_reason, .usage
  client.messages.parse(...)    -> same, plus .parsed_output (validated Pydantic model)
  client.messages.stream(...)   -> context manager with .text_stream and .get_final_message()

Script what it returns, then inspect what your code sent:

    from fake_llm import FakeAnthropic, reply, text, tool_use, RateLimited

    client = FakeAnthropic([
        reply(tool_use("get_weather", {"city": "Lagos"})),   # 1st call
        reply(text("It's 31°C in Lagos.")),                   # 2nd call
    ])
    ...your code calls client.messages.create(...) twice...
    client.calls[0]["messages"]   # exactly what you sent on the first call

A scripted item that is an exception (e.g. RateLimited()) is raised instead of returned.
Real code uses the real client; tests pass this one in. That's why exercises take `client` as a parameter.
"""
import itertools
import json
from types import SimpleNamespace

_ids = itertools.count(1)


def text(s: str):
    return SimpleNamespace(type="text", text=s)


def tool_use(name: str, input: dict, id: str | None = None):
    return SimpleNamespace(type="tool_use", id=id or f"toolu_{next(_ids):04d}", name=name, input=input)


def reply(*blocks, stop_reason: str | None = None, input_tokens: int = 100, output_tokens: int = 50):
    if stop_reason is None:
        stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return SimpleNamespace(
        type="message", role="assistant", content=list(blocks), stop_reason=stop_reason,
        model="fake", usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeAPIError(Exception):
    """Base for the fake errors. Like the real SDK, each has a status_code."""
    status_code = 500


class RateLimited(FakeAPIError):
    """Stands in for anthropic.RateLimitError (HTTP 429): safe to retry after waiting."""
    status_code = 429


class Overloaded(FakeAPIError):
    """Stands in for a 5xx server error: safe to retry."""
    status_code = 529


class BadRequest(FakeAPIError):
    """Stands in for anthropic.BadRequestError (HTTP 400): retrying won't help."""
    status_code = 400


class _Stream:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        for block in self._response.content:
            if block.type == "text":
                # Yield a few chunks per block so streaming code really loops.
                words = block.text.split(" ")
                for i, w in enumerate(words):
                    yield w if i == len(words) - 1 else w + " "

    def get_final_message(self):
        return self._response


class _Messages:
    def __init__(self, owner):
        self._owner = owner

    def _next(self, kwargs):
        self._owner.calls.append(kwargs)
        if not self._owner._script:
            raise AssertionError(f"FakeAnthropic: your code made call #{len(self._owner.calls)}, but the test only scripted "
                                 f"{len(self._owner.calls) - 1}. Is your loop stopping when it should?")
        item = self._owner._script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def create(self, **kwargs):
        return self._next(kwargs)

    def parse(self, *, output_format, **kwargs):
        resp = self._next({**kwargs, "output_format": output_format})
        raw = next(b.text for b in resp.content if b.type == "text")
        resp.parsed_output = output_format.model_validate(json.loads(raw))
        return resp

    def stream(self, **kwargs):
        return _Stream(self._next(kwargs))


class FakeAnthropic:
    def __init__(self, script=None):
        self._script = list(script or [])
        self.calls: list[dict] = []
        self.messages = _Messages(self)

    @property
    def remaining(self) -> int:
        return len(self._script)


if __name__ == "__main__":
    c = FakeAnthropic([reply(tool_use("t", {"a": 1})), RateLimited(), reply(text("hello there world"))])
    r = c.messages.create(model="m", messages=[])
    assert r.stop_reason == "tool_use" and r.content[0].input == {"a": 1}
    try:
        c.messages.create(model="m", messages=[])
        raise SystemExit("expected RateLimited")
    except RateLimited as e:
        assert e.status_code == 429
    with c.messages.stream(model="m", messages=[]) as s:
        assert "".join(s.text_stream) == "hello there world"
    assert len(c.calls) == 3 and c.remaining == 0
    print("fake_llm ok")
