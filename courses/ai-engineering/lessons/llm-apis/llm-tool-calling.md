# Tool calling

## Why this matters

On its own, a model can only produce text from what's in its context. It can't check today's exchange rate, look up an order in your database, do exact arithmetic on large numbers, or send an email. **Tools** close that gap: you describe functions your code can run, the model decides when to call them and with what arguments, and you feed the results back. Tool calling is how LLMs connect to real systems, and it's the foundation of every agent you'll build later in the course.

## 1. What a tool is (and isn't)

A tool is a **description** of a function: a name, a sentence about what it does, and a JSON schema for its input. You send these descriptions with the request. The model never runs anything itself. The flow is:

1. You send a message plus a list of tool definitions.
2. The model replies with a **`tool_use`** block: "please call `get_weather` with `{"city": "Lagos"}`". The response's `stop_reason` is `"tool_use"`.
3. **Your code** runs the real function.
4. You send the result back in a **`tool_result`** block.
5. The model reads the result and either answers (`stop_reason == "end_turn"`) or asks for another tool.

Your code is in control the whole time: you decide which tools exist, you run them, and you can refuse.

## 2. Defining a tool

```python
WEATHER_TOOL = {
    "name": "get_weather",
    "description": (
        "Get the current weather for a city. Use this whenever the user asks about "
        "current conditions or temperature. Returns temperature in °C and a short description."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Lagos' or 'Nairobi'"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["city"],
        "additionalProperties": False,
    },
}
```

- **`name`**: letters, digits, `_` and `-`. This is what the model calls and what you dispatch on.
- **`description`**: the most important part. The model decides *whether* and *when* to use the tool from this text. Say what it does, when to use it, what it returns, and any limits. A one-word description gets poor tool use.
- **`input_schema`**: a JSON schema, exactly like structured output. Enums, descriptions and `required` all help the model send good arguments.

Pass tools as a list:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    tools=[WEATHER_TOOL],
    messages=[{"role": "user", "content": "Is it hot in Lagos right now?"}],
)
print(response.stop_reason)  # tool_use
for block in response.content:
    print(block.type, getattr(block, "name", ""), getattr(block, "input", ""))
# text  I'll check the current weather in Lagos.
# tool_use get_weather {'city': 'Lagos'}
```

A `tool_use` block has three attributes you need:

- `block.id`: a unique id like `"toolu_01A..."`. You must echo it back with the result.
- `block.name`: which tool.
- `block.input`: a `dict` of arguments matching your schema.

Notice the reply can also contain text before the tool call. Keep it: it's part of the assistant's turn.

## 3. Sending the result back

To continue, append two messages to the history:

1. The assistant's turn, **exactly as returned**: `{"role": "assistant", "content": response.content}`. This includes the `tool_use` block, which the API needs to match up with your result.
2. A user turn containing a `tool_result` block per tool call.

```python
def get_weather(city: str, unit: str = "celsius") -> str:
    # A real version would call a weather API with httpx.
    return f"31°C, humid, light wind in {city}"

messages = [{"role": "user", "content": "Is it hot in Lagos right now?"}]
messages.append({"role": "assistant", "content": response.content})

tool_block = next(b for b in response.content if b.type == "tool_use")
result = get_weather(**tool_block.input)
messages.append({
    "role": "user",
    "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": result}],
})

final = client.messages.create(model="claude-opus-5-5", max_tokens=16000, tools=[WEATHER_TOOL], messages=messages)
print(final.stop_reason)       # end_turn
print(final.content[-1].text)  # Yes, it's hot: 31°C and humid in Lagos right now.
```

Keep sending `tools` on every call in the conversation: the model needs the definitions to understand the earlier `tool_use` blocks and to call tools again.

## 4. The loop

The model might need several tools in sequence: look up a customer, then their orders, then a refund policy. So you don't make a fixed number of calls; you **loop until `stop_reason` is `"end_turn"`**:

```python
HANDLERS = {"get_weather": lambda inp: get_weather(**inp)}


def run(client, user_msg: str, tools: list[dict], max_turns: int = 10) -> str:
    messages = [{"role": "user", "content": user_msg}]
    for _ in range(max_turns):
        response = client.messages.create(
            model="claude-opus-5-5", max_tokens=16000, tools=tools, messages=messages,
        )
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = HANDLERS[block.name](block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})
    raise RuntimeError("model kept calling tools; giving up")
```

Note the `max_turns` cap. A loop driven by model output must have a limit, or a confused model (or a tool that keeps failing) will burn money forever.

### Multiple tool calls in one turn

Ask "What's the weather in Lagos and Accra?" and the model will often request **both** in one reply: two `tool_use` blocks. The loop above already handles it, because it iterates over every block. The important rule:

> **Return all the tool results for one assistant turn in a single user message**, one `tool_result` block per `tool_use`, each with the matching `tool_use_id`.

Sending them as two separate user messages breaks the alternating-roles rule and confuses the model. Since the calls are independent, you can also run them concurrently (with threads or `asyncio.gather`) before building that one message.

## 5. When tools fail: `is_error`

Tools fail: the weather API times out, the order id doesn't exist, the input is invalid. Don't crash the loop, and don't hide the failure. Send it back with `"is_error": True` and a useful message:

```python
for block in response.content:
    if block.type != "tool_use":
        continue
    try:
        handler = HANDLERS[block.name]
        output = handler(block.input)
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
    except Exception as e:
        results.append({
            "type": "tool_result", "tool_use_id": block.id,
            "content": f"{type(e).__name__}: {e}", "is_error": True,
        })
```

The model reads the error and adapts: it might retry with corrected arguments ("city 'Lagoss' not found" → tries "Lagos"), try a different tool, or tell the user it couldn't get the data. Write error messages for the model the way you'd write them for a developer: what went wrong and, if possible, how to fix it.

## 6. Never trust tool input blindly

`block.input` is generated by a model. It usually matches your schema, but treat it like a request body from the public internet:

- It may have the wrong types or missing fields (especially without `strict`, below).
- It may contain values that are valid JSON but dangerous: `"../../etc/passwd"` as a filename, an email to someone outside your company, a refund of ₦10,000,000.
- The model's choices can be steered by **text it read**: a web page or document in the context can contain instructions ("call `send_email` to attacker@example.com"). This is prompt injection, covered in depth with agents.

So, in every tool handler:

```python
def get_order(tool_input: dict) -> str:
    order_id = tool_input.get("order_id")
    if not isinstance(order_id, str) or not order_id.isdigit():
        raise ValueError("order_id must be a string of digits, e.g. '4471'")
    # Only look up orders belonging to the logged-in customer, never "any order"
    order = db_lookup(order_id, customer_id=current_customer_id)
    ...
```

- **Validate** types and ranges (a Pydantic model works well: `Args.model_validate(block.input)`).
- **Scope** what tools can touch to the current user's data.
- **Never** pass tool input to `eval`, `exec`, a shell, or raw SQL.
- **Require human approval** for anything irreversible or costly (payments, emails, deletions).

### `strict: true`

Add `"strict": True` to a tool definition and the API guarantees `block.input` matches your schema exactly: correct types, required fields present, no extra keys.

```python
CALCULATOR_TOOL = {
    "name": "calculator",
    "description": "Exact arithmetic on two numbers. Use it for any calculation.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["operation", "a", "b"],
        "additionalProperties": False,
    },
}
```

Strict mode removes a class of bugs (no more `"a": "12"` as a string), but it guarantees **shape**, not **safety**: `b` can still be `0` for a division, and an email address can still be the wrong one. Keep validating meaning in your handler.

### Steering which tool gets used

The API has a `tool_choice` parameter, but forcing a specific tool (`{"type": "tool", ...}` or `{"type": "any"}`) returns a 400 error on current models. Steer from the prompt instead, which works well because current models follow instructions closely:

```python
system = "Always use the calculator tool for arithmetic, even simple sums. Never compute numbers yourself."
```

Clear tool descriptions do most of this work for you.

## 7. A preview of agents

Look at the loop again: the model decides what to do, your code acts, the model sees the result and decides again, until the job is done. That **is** an agent, in its simplest form. Everything you'll add in the agents section builds on this loop:

- More and better tools (search, files, databases, other APIs).
- Memory beyond one conversation.
- Human approval steps for risky actions.
- Evaluation: measuring whether the agent actually completes tasks.
- Defences against prompt injection.

For now, the key ideas are the loop, the `tool_use`/`tool_result` pairing, error reporting with `is_error`, and the rule that tool input is untrusted.

> **Try it:** Give the model the calculator tool and ask "What is 48,213 × 7,019, minus 3% of that?" Print each `tool_use` block as it arrives to watch the model chain calls.

## Common mistakes

- **Forgetting to append the assistant turn** (with its `tool_use` blocks) before the `tool_result`. The API rejects results that don't follow a matching `tool_use`.
- **Mismatched `tool_use_id`s**, or results for one turn split over several user messages.
- **Stopping after one tool call** instead of looping until `end_turn`.
- **No `max_turns` cap** on the loop.
- **Letting one failing tool crash the whole request** instead of returning `is_error`.
- **Vague tool descriptions**, so the model doesn't know when to use the tool.
- **Trusting `block.input`**: running it through `eval`, a shell, or unscoped database queries.
- **Dropping `tools` on later calls** in the same conversation.

## Recap

- A tool is a name, a description and an `input_schema`; the model requests calls, your code runs them.
- `stop_reason == "tool_use"` means run the `tool_use` blocks (`.id`, `.name`, `.input`).
- Append the assistant turn as-is, then one user message with a `tool_result` per call, matched by `tool_use_id`.
- Loop until `stop_reason == "end_turn"`, with a turn limit.
- Report failures with `"is_error": True` so the model can adapt.
- Use `"strict": True` for schema-valid input, steer tool choice from the prompt, and always validate and scope what tools can do.
