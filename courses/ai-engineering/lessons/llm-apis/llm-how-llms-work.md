# How LLMs work (the parts an engineer needs)

## Why this matters

You don't need to train a model to build with one, but you do need an accurate mental model of what it does with your request. Nearly every practical question in this section comes back to a few facts: the model reads **tokens**, it predicts **one token at a time**, it can only see what fits in its **context window**, and it **remembers nothing** between calls. Get these right and cost, latency, "why did it forget?" and "why did it answer differently this time?" all stop being mysteries.

## 1. Text becomes tokens

A model doesn't read characters or words. It reads **tokens**: chunks of text from a fixed vocabulary of tens of thousands of pieces. Common words are usually one token; rare words, names and code get split into several. Spaces and punctuation are often glued to the next piece.

```
"The cat sat on the mat."  →  ["The", " cat", " sat", " on", " the", " mat", "."]
"Okafor's tokenisation"    →  ["Ok", "af", "or", "'s", " token", "isation"]   (illustrative split)
```

Each token is really an integer id. The model sees a list of integers, not letters, which is why LLMs are sometimes clumsy at "how many r's are in strawberry?": the letters are hidden inside tokens.

Tokens matter to you for three reasons:

1. **You pay per token**: input tokens (what you send) and output tokens (what comes back) are priced separately, and output is more expensive.
2. **Limits are in tokens**: the context window and `max_tokens` are both counted in tokens.
3. **Speed is in tokens**: the model generates output one token at a time, so long answers take longer.

A rough rule for English is **1 token ≈ 4 characters ≈ ¾ of a word**. It's good enough for estimates:

```python
import math

def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)

print(estimate_tokens("The cat sat on the mat."))  # 6
print(estimate_tokens("x" * 4000))                  # 1000
```

For exact numbers, ask the API. Token counting is free and doesn't run the model:

```python
import anthropic

client = anthropic.Anthropic()
count = client.messages.count_tokens(
    model="claude-opus-5-5",
    messages=[{"role": "user", "content": "The cat sat on the mat."}],
)
print(count.input_tokens)
```

> **Note:** Different model families use different tokenisers, so the same text can be a different number of tokens on different models. Code, non-English text and long numbers usually cost more tokens per character than plain English.

## 2. The model predicts the next token

Underneath everything, a language model does one job: **given a sequence of tokens, output a probability for every token in the vocabulary being the next one.**

To produce a whole answer, the system runs that in a loop:

1. Feed in the tokens so far.
2. Get a probability distribution over the next token.
3. Pick one token from it.
4. Append it and repeat, until the model emits a special "end" token or hits `max_tokens`.

Here is the same loop with a toy "model" that is just a lookup table of which word follows which. A real LLM replaces the table with a neural network that takes the *entire* preceding text into account, but the outer loop is the same:

```python
import random

# Toy model: probabilities of the next word given only the previous word.
NEXT = {
    "<start>": {"the": 0.7, "a": 0.3},
    "the": {"cat": 0.5, "dog": 0.5},
    "a": {"cat": 0.4, "dog": 0.6},
    "cat": {"sat": 0.8, "<end>": 0.2},
    "dog": {"ran": 0.7, "<end>": 0.3},
    "sat": {"<end>": 1.0},
    "ran": {"<end>": 1.0},
}

def generate(max_tokens: int = 10) -> list[str]:
    out, token = [], "<start>"
    for _ in range(max_tokens):
        options = NEXT[token]
        token = random.choices(list(options), weights=list(options.values()))[0]
        if token == "<end>":
            break
        out.append(token)
    return out

for _ in range(3):
    print(" ".join(generate()))
# the cat sat
# a dog ran
# the dog        (yours will differ: it's random)
```

Two things fall out of this picture:

- **The model writes left to right and can't go back.** It commits to each token. That's why asking it to reason before answering (covered in the prompting lesson) helps: the reasoning tokens become part of the input for the final answer.
- **`max_tokens` is a hard stop.** If the loop hits it, the answer is cut off mid-sentence. The API tells you this happened with `stop_reason == "max_tokens"`.

## 3. Why outputs vary

Step 3 of the loop says "pick one token". Choosing the single most likely token every time (greedy decoding) tends to give repetitive, bland text, so models **sample** from the distribution instead. Sampling means two identical requests can produce different answers.

You can see how a distribution is shaped by "temperature" with a few lines of Python. The network outputs raw scores (logits); softmax turns them into probabilities, and dividing by a temperature first makes the distribution sharper (low T) or flatter (high T):

```python
import math

def softmax(scores: list[float], temperature: float = 1.0) -> list[float]:
    scaled = [s / temperature for s in scores]
    m = max(scaled)
    exps = [math.exp(s - m) for s in scaled]
    total = sum(exps)
    return [e / total for e in exps]

logits = [2.0, 1.0, 0.1]  # scores for three candidate tokens
print([round(p, 2) for p in softmax(logits, 1.0)])   # [0.66, 0.24, 0.1]
print([round(p, 2) for p in softmax(logits, 0.2)])   # [0.99, 0.01, 0.0]
print([round(p, 2) for p in softmax(logits, 2.0)])   # [0.5, 0.3, 0.19]
```

> **Note:** Older Claude models let you set `temperature`, `top_p` and `top_k` on the request. Current models don't accept them (the API returns a 400 error), so you won't use them in this course. Treat variation as a fact of life and design for it.

What "design for it" means in practice:

- **Never depend on exact wording.** If code needs to read the answer, ask for a structure (XML tags, JSON) and parse it. The structured output lesson covers this properly.
- **Test prompts on several inputs, several times.** One good answer proves little.
- **Validate everything.** Treat model output like user input from the internet.

## 4. Training vs inference

Two phases, very different costs:

- **Training** is how the model learned. First, *pre-training* on a huge amount of text teaches it to predict the next token, and in doing so it soaks up grammar, facts, code and reasoning patterns. Then *post-training* (fine-tuning on examples and human feedback) turns that raw predictor into an assistant that follows instructions and declines harmful requests. Training takes months and enormous compute, and it sets the model's **weights**: billions of fixed numbers.
- **Inference** is using the trained model: running your tokens through those fixed weights to get predictions. Every API call is inference. **Nothing you send changes the weights.**

Consequences you'll hit constantly:

- The model's built-in knowledge stops at its **training cutoff**. It doesn't know about yesterday's news, your company's documents or your database unless you put that information in the request. (Feeding it the right information at request time is called retrieval-augmented generation, or RAG, and has its own section later.)
- Telling a model "remember this for next time" does nothing on its own. It can't learn from your conversation.

## 5. The context window, and "the model only sees what you send"

The **context window** is the maximum number of tokens the model can look at in one call: your system prompt, the whole conversation, any documents, tool definitions, **plus** the tokens it generates. Current Claude models have windows in the hundreds of thousands of tokens (see the models overview in the resources for exact figures), which is a lot, but not infinite, and you pay for every input token on every call.

The single most important fact about LLM APIs:

> **The API is stateless. Each request is independent. The model only sees the text in that request.**

There's no session on the server holding your chat. When a chatbot "remembers" what you said three messages ago, it's because the app **re-sent** those three messages. In code, a conversation is just a list you keep growing:

```python
history = []

def add_turn(user_text: str, assistant_text: str) -> None:
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})

add_turn("My name is Ada.", "Nice to meet you, Ada!")
add_turn("What's my name?", "Your name is Ada.")
print(len(history))  # 4 -- all four go out with the next request
```

What follows from statelessness:

- **Cost grows with conversation length.** Turn 20 of a chat re-sends turns 1–19 as input tokens.
- **Long chats eventually overflow.** You must trim, summarise or drop old turns (the practice exercise in this lesson does the simplest version).
- **You control the memory.** You can edit history, inject documents, or start fresh. That's a feature: it's how RAG and agents work.
- **Missing context is the #1 cause of bad answers.** If the model needs a fact to do the job, it must be in the request.

## 6. Transformers and attention, intuitively

The neural network inside modern LLMs is a **transformer**. You don't need the maths to use one, but the intuition helps.

1. **Embeddings.** Each token id is turned into a long vector of numbers (an embedding). Tokens with related meanings end up with vectors pointing in similar directions.
2. **Attention.** In each layer, every token looks at all the earlier tokens and decides which ones matter for understanding it. In "The bank of the river was muddy", attention lets "bank" pull in information from "river" so its vector shifts towards the riverside meaning, not the money one. Each token builds a *query* ("what am I looking for?"), every token offers a *key* ("what do I contain?") and a *value* ("what do I pass on?"). Matching queries against keys gives the attention weights.
3. **Feed-forward layers** then process each token's updated vector on its own; this is where a lot of stored knowledge seems to live.
4. **Many layers deep.** Attention plus feed-forward is repeated dozens of times. By the last layer, the vector at the final position holds enough about the whole text to score every possible next token.

Here is attention for one token, in plain numpy, so the idea is concrete:

```python
import numpy as np

def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()

# 3 earlier tokens, each with a 4-dimensional key and value
keys = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0.9, 0.1, 0, 0]])
values = np.array([[10, 0], [0, 10], [9, 1]])
query = np.array([1, 0, 0, 0])  # "I'm looking for things like token 0"

scores = keys @ query / np.sqrt(4)   # similarity of the query to each key
weights = softmax(scores)
print(weights.round(2))              # [0.39 0.24 0.37] -> tokens 0 and 2 matter most
print(weights @ values)              # [7.26 2.74]: a blend of the values, weighted by relevance
```

Why this matters to an engineer:

- Attention compares every token with every other, so **longer inputs cost more compute**, which is part of why you pay per input token.
- Everything in the context can influence everything else. **Irrelevant or conflicting text in the prompt can distract the model.** Send what's needed, clearly separated.
- Instructions, documents and user messages are all just tokens to the model. It has no hard boundary between "your instructions" and "the data". That's the root of prompt injection, which you'll study with agents.

The 3Blue1Brown video for this lesson animates exactly this process and is worth watching in full. Karpathy's talk gives the bigger picture: training stages, what models can and can't do, and where things are heading.

## Common mistakes

- **Assuming the model remembers.** It doesn't. If a follow-up question gets a confused answer, check that you sent the history.
- **Estimating cost in words, not tokens,** or forgetting that output tokens cost several times more than input tokens.
- **Setting `max_tokens` too low** and shipping truncated answers. Check `stop_reason`.
- **Treating one good output as proof.** Outputs vary; test on several inputs.
- **Expecting up-to-date knowledge.** Anything after the training cutoff, or private to you, must go in the prompt.
- **Stuffing the context "just in case".** More text costs more and can make answers worse.

## Recap

- Models read **tokens** (≈ 4 characters each in English); you pay per input and output token.
- Generation is a loop: predict a distribution over the next token, sample one, append, repeat, until an end token or `max_tokens`.
- Sampling is why outputs vary. Current Claude models don't expose temperature; design with parsing, validation and tests instead.
- **Training** sets fixed weights; **inference** (every API call) uses them and changes nothing.
- The **context window** holds everything for one call. The API is **stateless**: resend the history every time.
- Transformers use **attention** so each token can draw on the relevant earlier tokens; everything in the prompt can affect the answer.
