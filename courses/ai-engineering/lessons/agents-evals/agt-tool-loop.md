# A production-grade tool loop

## Why this matters

The loop from *Tool calling* works in a demo. In production it meets tools that time out, models that ask for three tools at once, responses cut off mid-tool-call, server-side pauses, refusals, and a model that keeps calling the same failing tool until your bill arrives. This lesson turns that loop into one you'd run for paying customers: tools defined once from Python functions, every `stop_reason` handled, every step logged, and a budget that stops runaway runs. Then you'll see the SDK helper that does the common parts for you, and when it's not enough.

## 1. A tool registry from Python functions

Hand-written schemas drift: someone adds a parameter to the function and forgets the JSON. Instead, generate the schema from the function itself. Python already knows the parameter names, their types (from type hints), which ones have defaults, and the docstring.

```python
import inspect
import typing
from typing import Literal

TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


def schema_for(fn) -> dict:
    hints = typing.get_type_hints(fn)          # resolves string annotations too
    properties, required = {}, []
    for name, param in inspect.signature(fn).parameters.items():
        hint = hints[name]
        if typing.get_origin(hint) is Literal:
            properties[name] = {"type": "string", "enum": list(typing.get_args(hint))}
        else:
            properties[name] = {"type": TYPES[hint]}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    doc = inspect.getdoc(fn) or ""
    return {
        "name": fn.__name__,
        "description": doc.split("\n\n")[0],
        "input_schema": {"type": "object", "properties": properties,
                         "required": required, "additionalProperties": False},
    }


def get_order(order_id: str, include_items: bool = False) -> str:
    """Look up one order by id. Returns status, total and (optionally) line items."""
    ...

print(schema_for(get_order)["input_schema"]["required"])   # ['order_id']
```

A **registry** collects these with a decorator, so defining a tool and registering it is one step:

```python
class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def tool(self, fn):
        self._tools[fn.__name__] = (fn, schema_for(fn))
        return fn                                       # the function still works normally

    def schemas(self) -> list[dict]:
        return [s for _, s in self._tools.values()]

    def handlers(self) -> dict:
        return {name: (lambda inp, f=fn: str(f(**inp))) for name, (fn, _) in self._tools.items()}


registry = ToolRegistry()

@registry.tool
def get_weather(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
    """Get the current weather for a city."""
    return f"31°C in {city}"
```

You decorated functions in *Decorators and context managers*; this is the same idea put to work.

### Or let Pydantic do it

For richer inputs (nested objects, lists, ranges), build a Pydantic model and use its schema, as in *Structured output with Pydantic*. Pydantic can even build the model from the function's signature for you:

```python
from typing import Literal

from pydantic import Field, TypeAdapter, validate_call


def search_orders(customer_email: str, status: Literal["open", "shipped", "refunded"] | None = None,
                  limit: int = Field(10, ge=1, le=50)) -> str:
    """Find a customer's orders, newest first."""
    ...

schema = TypeAdapter(search_orders).json_schema()   # JSON schema of the arguments
print(schema["required"], schema["properties"]["limit"])
# ['customer_email'] {'default': 10, 'maximum': 50, 'minimum': 1, 'title': 'Limit', 'type': 'integer'}

safe_search = validate_call(search_orders)          # validates the model's input before running
safe_search("ada@example.com", limit=5000)
# ValidationError: limit  Input should be less than or equal to 50
```

`validate_call` is worth using either way: the model's `block.input` is untrusted, and this rejects `limit=5000` with a clear error you can send back as `is_error`.

## 2. Parallel calls, errors and a turn budget

You already know the core rules from *Tool calling*; here they are as one checklist, since a production loop must do all of them:

- Append the assistant turn **exactly as returned** (`response.content`).
- Run **every** `tool_use` block in the reply, and return **all** results in **one** user message.
- A tool that raises, or an unknown tool name, gets `"is_error": True` with a message that helps the model recover.
- A **turn budget** (`max_turns`) stops a model that loops.

When the model asks for several independent tools, you can run them concurrently. With synchronous handlers, a thread pool is the least code:

```python
from concurrent.futures import ThreadPoolExecutor

calls = [b for b in response.content if b.type == "tool_use"]
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(lambda b: run_tool(handlers, b), calls))   # map keeps the order
messages.append({"role": "user", "content": results})
```

Write error messages for the model. `"KeyError: 'A9'"` tells it little; `"No order with id 'A9'. Order ids look like 'A1042'; use search_orders to find them."` lets it fix its own mistake on the next turn.

## 3. Every stop reason

`stop_reason` tells you **why** the model stopped. A robust loop handles each one deliberately:

| `stop_reason` | Meaning | What your loop does |
|---|---|---|
| `end_turn` | The model finished its answer. | Done: return the text. |
| `tool_use` | It wants tools run. | Run them, send results, loop. |
| `max_tokens` | Output hit your `max_tokens` limit. | If the last block is a cut-off `tool_use`, retry with a bigger limit. Otherwise the text is truncated: report that. |
| `pause_turn` | The API paused a long-running turn (this happens with server-side tools such as web search, which run on Anthropic's side). | Append the assistant content unchanged and call again to let it continue. |
| `refusal` | The model declined, for safety reasons. | Stop. Don't retry the same request in a loop; log it, and show the user a clear message. |
| `stop_sequence` | It produced one of your `stop_sequences`. | Treat as done (you asked for it). |

Here's the loop with all of that in place:

```python
import logging

log = logging.getLogger("agent")


def run_agent(client, task, tools, handlers, *, model="claude-opus-5-5", max_turns=10, max_tokens=4096):
    messages = [{"role": "user", "content": task}]
    for turn in range(1, max_turns + 1):
        response = client.messages.create(model=model, max_tokens=max_tokens, tools=tools, messages=messages)
        reason = response.stop_reason
        log.info("turn %d stop_reason=%s in=%d out=%d", turn, reason,
                 response.usage.input_tokens, response.usage.output_tokens)

        if reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = [run_tool(handlers, b) for b in response.content if b.type == "tool_use"]
            messages.append({"role": "user", "content": results})
        elif reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})   # just continue
        elif reason == "max_tokens":
            if response.content and response.content[-1].type == "tool_use":
                max_tokens *= 2                     # cut off mid-tool-call: retry with more room
            else:
                return {"status": "truncated", "text": text_of(response)}
        elif reason == "refusal":
            return {"status": "refused", "text": text_of(response)}
        else:                                       # end_turn, stop_sequence
            return {"status": "done", "text": text_of(response)}
    return {"status": "max_turns", "text": ""}
```

Three design choices to notice:

- It **returns a status** rather than raising for expected outcomes. The caller (an API route, a job queue) decides what "truncated" or "max_turns" means for the user. Unexpected failures (a 400 from the API) still raise.
- The `max_tokens` retry doesn't append the cut-off turn: a half-written `tool_use` has invalid input, so you re-ask with room to finish it.
- A `pause_turn` is not the model asking you for anything. You simply send its own content back so it can carry on.

> **Note:** Network errors and 429/529 responses are a different layer. The SDK already retries those twice by default; wrap the `create` call in the retry helper from *Errors, retries and cost control* if you need more.

## 4. Log every step

When an agent gives a wrong answer, the question is always "what did it do?" Answer it with structured logs: one record per turn and per tool call.

```python
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("agent")


def run_tool(handlers, block) -> dict:
    start = time.perf_counter()
    result = {"type": "tool_result", "tool_use_id": block.id}
    try:
        result["content"] = str(handlers[block.name](block.input))
    except Exception as e:
        result |= {"content": f"{type(e).__name__}: {e}", "is_error": True}
    log.info(json.dumps({
        "event": "tool_call", "tool": block.name, "input": block.input,
        "is_error": result.get("is_error", False),
        "ms": round((time.perf_counter() - start) * 1000),
        "output_preview": result["content"][:200],
    }))
    return result
# {"event": "tool_call", "tool": "get_order", "input": {"order_id": "A1"}, "is_error": false, "ms": 12, ...}
```

Log the tool name, input, error flag, duration, a preview of the output, and per-turn token usage. JSON lines are easy to grep now and to ship to a tracing tool later. Also return the list of tool calls from `run_agent`: your evals will assert on it ("did the agent call `refund` with the right order id?").

> **Note:** Don't log secrets or full personal data. Log ids and previews, not whole customer records.

## 5. The shortcut: the SDK's tool runner

Once you understand the loop, the Anthropic SDK can run it for you. `@beta_tool` builds the schema from the signature and docstring (exactly what your registry does) and `tool_runner` handles the call, run, append, repeat cycle:

```python
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()


@beta_tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location.

    Args:
        location: City, e.g. Lagos.
        unit: "celsius" or "fahrenheit".
    """
    return f"31°C in {location}"


runner = client.beta.messages.tool_runner(
    model="claude-opus-5-5", max_tokens=16000, tools=[get_weather],
    messages=[{"role": "user", "content": "Weather in Paris and Lagos?"}],
)
for message in runner:          # each iteration is one model turn
    print(message.stop_reason, [b.type for b in message.content])
```

The runner also turns exceptions from your tools into `is_error` results, and accepts `max_iterations` as a turn budget. Use `@beta_async_tool` with `async def` functions and the async client.

When to use which:

| Use the tool runner when | Write your own loop when |
|---|---|
| Tools are plain functions with no approval step | Some tools need human approval before they run |
| You want to prototype quickly | You need custom logging, tracing or per-tool timeouts |
| The defaults for errors and stopping suit you | You need spending limits, dry-run mode, or to stop on specific results |

You'll need those right-hand features in *Humans in the loop*, which is why you built the loop yourself first.

> **Try it:** In the practice editor, write `run_agent` so it passes every stop-reason test. Then write the registry and feed its `schemas()` straight into `tools=`.

## Common mistakes

- **Treating every non-`tool_use` stop as success.** A `max_tokens` stop means the answer is cut off; a `refusal` means there is no answer.
- **Appending a truncated `tool_use` turn** and sending a result for it. Retry with a larger `max_tokens` instead.
- **Adding a user message after `pause_turn`.** Just send the assistant content back.
- **Raising on `max_turns` deep inside a web request** and returning a 500. Return a status and decide at the edge.
- **Schemas written by hand** that no longer match the function.
- **Logging nothing**, or logging everything including customer data.
- **Reaching for the tool runner when you need approvals**, then fighting it.

## Recap

- Generate tool schemas from type hints and docstrings (or Pydantic) so code and schema can't drift; validate input with `validate_call`.
- Run every `tool_use` block, answer them all in one message, use `is_error` with helpful messages, and cap turns.
- Handle each `stop_reason`: `end_turn` done, `tool_use` run tools, `max_tokens` retry or report truncation, `pause_turn` continue, `refusal` stop.
- Log each turn and tool call as structured data, and return the tool calls for evals.
- The SDK's `tool_runner` with `@beta_tool` runs the standard loop for you; write your own when you need approvals, budgets or custom tracing.
