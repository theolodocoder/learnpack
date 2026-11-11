# Your first API call

## Why this matters

Every LLM product you'll build (chatbots, extractors, RAG systems, agents) is, at its core, a program that sends a list of messages to an API and reads back a response. This lesson covers that one call thoroughly: how to authenticate safely, what to send, what comes back, how conversations work when the API remembers nothing, and how to know what each call costs. Clients will ask "how much will this cost per month?" and you should be able to answer with arithmetic, not guesses.

## 1. Get an API key and keep it secret

1. Sign in to the Claude Console at `platform.claude.com`, add billing credit, and create a key under **Settings → API keys**. It starts with `sk-ant-`.
2. Put it in a file called `.env` in your project root:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Add `.env` to `.gitignore` **before your first commit**. Bots scan GitHub for leaked keys within minutes, and anyone with your key spends your money.

In your own projects, load the file with `python-dotenv`:

```python
from dotenv import load_dotenv
import anthropic

load_dotenv()                  # copies ANTHROPIC_API_KEY from .env into the environment
client = anthropic.Anthropic() # reads ANTHROPIC_API_KEY automatically
```

Create the client **once** and reuse it. It holds a pool of HTTP connections, so making a new one per request is wasteful.

> **Note:** Inside this platform's practice editor, **Run** already passes your key from the repo's `.env`, so you don't need `load_dotenv()` there. **Check** never uses the key: tests run against a fake client, offline and free.

## 2. The basic call

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    system="You are a concise assistant.",
    messages=[{"role": "user", "content": "In one sentence, what is an API?"}],
)

for block in response.content:
    if block.type == "text":
        print(block.text)
print(response.usage.input_tokens, response.usage.output_tokens, response.stop_reason)
# An API is a defined way for one program to request data or actions from another.
# 23 19 end_turn
```

The four arguments you'll use on almost every call:

| Argument | What it does |
|---|---|
| `model` | Which model runs the request (see section 7). |
| `max_tokens` | The **maximum** number of output tokens. It's a ceiling, not a target: you pay only for what's generated. Too low and answers get cut off. |
| `system` | Instructions that frame the whole conversation: role, rules, tone, output format. Optional. |
| `messages` | The conversation so far: a list of `{"role": ..., "content": ...}` dicts. |

## 3. Roles and the system prompt

`messages` alternates between two roles:

- `"user"`: what the human (or your program, acting as the human) says.
- `"assistant"`: what the model said earlier.

**The first message must be `user`.** The `system` prompt is separate: it's not a message, it's a top-level argument.

Put stable instructions in `system` and the specific request in the user message:

```python
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=2000,
    system=(
        "You are a support assistant for Paystack-style payment APIs. "
        "Answer in at most three sentences. If you don't know, say so."
    ),
    messages=[{"role": "user", "content": "Why would a charge return 'insufficient funds'?"}],
)
```

The system prompt is the right home for anything that should apply to every turn: who the assistant is, house rules, formatting requirements, background facts about your product.

## 4. Multi-turn conversations: you resend everything

As the previous lesson stressed, the API is **stateless**. To continue a conversation, send the full history, including the assistant's previous replies, plus the new user message:

```python
history = [
    {"role": "user", "content": "My name is Ada and I'm learning Python."},
    {"role": "assistant", "content": "Nice to meet you, Ada! How can I help with Python?"},
    {"role": "user", "content": "What's my name, and what am I learning?"},
]
response = client.messages.create(model="claude-opus-5-5", max_tokens=1000, messages=history)
print(response.content[0].text)
# Your name is Ada and you're learning Python.
```

A minimal chat loop keeps appending to the list:

```python
import anthropic

client = anthropic.Anthropic()
history: list[dict] = []

while True:
    user_text = input("you> ")
    if user_text in {"quit", "exit"}:
        break
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model="claude-haiku-5-5", max_tokens=2000,
        system="You are a friendly tutor.", messages=history,
    )
    reply = "".join(b.text for b in response.content if b.type == "text")
    history.append({"role": "assistant", "content": reply})
    print("claude>", reply)
```

> **Try it:** Paste this into the practice editor, delete the `history.append` for the assistant reply, and see how the conversation breaks: you'll send two `user` messages in a row and the model never sees its own previous answers.

Because you own the history, you can also *fabricate* it: put example exchanges in `messages` to show the model a pattern, or seed a conversation from a database. The model can't tell the difference.

## 5. Reading the response

`response` is a `Message` object. The fields you'll use:

```python
response.id            # "msg_01..." -- log it; support will ask for it
response.model         # the model that answered
response.content       # a LIST of content blocks
response.stop_reason   # why generation stopped
response.usage         # token counts
```

### Content is a list of blocks

`content` isn't a string. It's a list, because a reply can mix types: text, requests to use tools (`tool_use`), and on current models, thinking blocks. Always check `block.type`:

```python
def reply_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")
```

`response.content[0].text` works for simple replies, but it breaks the day the first block is something other than text. Use the loop.

### `stop_reason`

| Value | Meaning | What to do |
|---|---|---|
| `"end_turn"` | The model finished naturally. | Use the answer. |
| `"max_tokens"` | It hit your `max_tokens` limit mid-answer. | Raise the limit, ask for shorter output, or continue. Don't silently ship a truncated answer. |
| `"stop_sequence"` | It produced one of your `stop_sequences`. | Expected if you set them. |
| `"tool_use"` | It wants you to run a tool. | See the tool calling lesson. |
| `"refusal"` | It declined for safety reasons. | Handle gracefully. |

```python
if response.stop_reason == "max_tokens":
    print("Warning: answer was cut off")
```

### `usage`

```python
response.usage.input_tokens   # tokens you sent (system + messages + tools)
response.usage.output_tokens  # tokens it generated (including any thinking)
```

These are the numbers you're billed on.

## 6. Cost maths

Prices are quoted **per million tokens**, with output priced higher than input:

| Model | Input / 1M tokens | Output / 1M tokens |
|---|---|---|
| `claude-opus-5-5` | $4.00 | $20.00 |
| `claude-sonnet-5-5` | $2.00 | $10.00 |
| `claude-haiku-5-5` | $0.10 | $0.50 |

The formula:

```
cost = input_tokens · input_price / 1,000,000  +  output_tokens · output_price / 1,000,000
```

In code:

```python
PRICES = {  # (input, output) dollars per 1M tokens
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, out = PRICES[model]
    return (input_tokens * inp + output_tokens * out) / 1_000_000

print(cost_usd("claude-opus-5-5", 2_000, 500))   # 0.018
print(cost_usd("claude-haiku-5-5", 2_000, 500))  # 0.00045
```

Now scale it. A support bot handles 3,000 chats a day, each averaging 6 turns. Because history is resent, input grows each turn; say the average call sends 1,500 input tokens and gets 200 output tokens:

```python
calls_per_day = 3_000 * 6
for model in PRICES:
    daily = calls_per_day * cost_usd(model, 1_500, 200)
    print(f"{model}: ${daily:,.2f}/day  ${daily * 30:,.0f}/month")
# claude-opus-5-5: $180.00/day  $5,400/month
# claude-sonnet-5-5: $90.00/day  $2,700/month
# claude-haiku-5-5: $4.50/day  $135/month
```

That 40× gap between Opus and Haiku is why model choice is an engineering decision, not a preference.

## 7. Choosing a model

| Model | Best for | Trade-off |
|---|---|---|
| **Opus 5.5** (`claude-opus-5-5`) | Hard reasoning, complex code, agents with many steps, anything where a wrong answer is expensive. The default in this course's examples. | Most expensive; slower. |
| **Sonnet 5.5** (`claude-sonnet-5-5`) | A strong middle tier: most production workloads that need good quality at half Opus's price. | |
| **Haiku 5.5** (`claude-haiku-5-5`) | High-volume, simple tasks: classification, extraction from clean text, routing, quick experiments. | Weaker on hard reasoning. |

A practical approach:

1. **Prototype with Haiku** while you're iterating on code; it's cheap enough to run hundreds of times.
2. **Measure quality** on a set of real inputs with the best model (Opus) to learn what "good" looks like.
3. **Step down** to Sonnet or Haiku and check whether quality holds. Use the cheapest model that passes.
4. Mix models: Haiku to classify incoming requests, Opus only for the hard ones.

Make the model a parameter or config value, never a string scattered through your code, so switching is a one-line change.

## Putting it together

```python
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}


def ask(question: str, model: str = "claude-haiku-5-5") -> str:
    response = client.messages.create(
        model=model, max_tokens=2000,
        system="You are a concise assistant. Answer in plain English.",
        messages=[{"role": "user", "content": question}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    inp, out = PRICES[model]
    cost = (response.usage.input_tokens * inp + response.usage.output_tokens * out) / 1_000_000
    print(f"[{response.stop_reason}, {response.usage.input_tokens} in / {response.usage.output_tokens} out, ${cost:.5f}]")
    return text


print(ask("What does HTTP status 429 mean?"))
```

## Common mistakes

- **Committing `.env`** or pasting your key into code. Use `.gitignore` from day one; if a key leaks, revoke it in the Console immediately.
- **Starting `messages` with an assistant turn**, or sending two `user` messages in a row because you forgot to append the reply.
- **Reading `response.content` as a string.** It's a list of blocks; filter for `type == "text"`.
- **Ignoring `stop_reason`.** A `"max_tokens"` stop means the answer is incomplete.
- **Creating a new client per request.** Create one and reuse it.
- **Hard-coding Opus everywhere** and being surprised by the bill. Estimate cost before you ship.
- **Putting per-request data in the system prompt** and stable rules in the user message. Rules go in `system`; the specific task goes in `messages`.

## Recap

- Keep the key in `.env`, git-ignored; `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY`.
- `client.messages.create(model=..., max_tokens=..., system=..., messages=[...])` is the core call.
- Roles alternate `user`/`assistant`, starting with `user`. The system prompt is separate.
- The API is stateless: append each reply to your history and resend it all.
- `response.content` is a list of blocks; check `stop_reason`; bill from `usage`.
- Cost = tokens × price per million; Opus $4/$20, Sonnet $2/$10, Haiku $0.10/$0.50.
- Prototype cheap, measure quality, then use the cheapest model that's good enough.
