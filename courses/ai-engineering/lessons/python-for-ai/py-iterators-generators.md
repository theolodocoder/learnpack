# Iterators and generators

## Why this matters

When you stream an answer from Claude, you don't get one string: you get a sequence of small chunks over several seconds, and you display each one as it arrives. In code, that's a `for` loop over an iterator. The same pattern lets you process a 5 GB log file or a million documents without loading them all into memory, and lets you split documents into batches for an embedding API. Understanding iterators and generators turns all of these into simple loops.

## Iterables and iterators

An **iterable** is anything you can loop over: lists, strings, dicts, files, ranges. An **iterator** is the object that actually does the looping: it hands out one item at a time and remembers where it is.

`iter(x)` gets an iterator from an iterable, and `next(it)` asks for the next item. When there are no more, `next` raises `StopIteration`.

```python
names = ["Ada", "Grace"]        # iterable
it = iter(names)                # iterator
print(next(it))                 # Ada
print(next(it))                 # Grace
next(it)                        # raises StopIteration
```

A `for` loop does exactly this for you: it calls `iter()` once, then `next()` until `StopIteration`.

The important difference: an iterable like a list can be looped over many times. An iterator is **used up** after one pass.

```python
it = iter([1, 2, 3])
print(list(it))   # [1, 2, 3]
print(list(it))   # []   <- already exhausted
```

Files are iterators over their lines, and `zip`, `map`, `filter` and `enumerate` all return iterators. So does a streamed LLM response.

## Generators: functions that `yield`

Writing an iterator class by hand is tedious. A **generator function** is the easy way: any function containing `yield` returns a generator, which is an iterator.

```python
def count_up(limit: int):
    n = 1
    while n <= limit:
        yield n          # hand out n, then pause right here
        n += 1

gen = count_up(3)
print(gen)              # <generator object count_up at 0x...>
print(next(gen))        # 1
print(list(gen))        # [2, 3]
```

Each `yield` hands one value to the caller and **pauses** the function, keeping all its local variables. The next `next()` resumes right after the `yield`. When the function returns, the generator is finished.

That pause is the key property: a generator does no work until someone asks for the next item. That's called **lazy** evaluation.

```python
def noisy():
    print("start")
    yield 1
    print("after 1")
    yield 2

g = noisy()       # prints nothing yet: the body hasn't started
print(next(g))    # start / 1
print(next(g))    # after 1 / 2
```

> **Note:** Because the body doesn't run until the first `next()`, any check at the top of a generator function (like `if size < 1: raise ValueError`) also doesn't run until someone starts looping. If you want the error immediately, check in a normal function that then returns a generator. You'll do this in the batching exercise.

### Generator expressions

A comprehension in round brackets is a **generator expression**: same syntax, but lazy.

```python
squares_list = [n * n for n in range(1_000_000)]   # builds a million-item list now
squares_gen = (n * n for n in range(1_000_000))    # builds nothing yet
print(sum(n * n for n in range(1_000_000)))        # brackets can be dropped inside a call
```

`sum`, `max`, `any`, `all`, `"".join` and friends accept any iterable, so feeding them a generator expression avoids building a temporary list.

### `yield from`

`yield from other` yields every item of another iterable, which is handy for delegating:

```python
def all_lines(paths):
    for path in paths:
        with open(path, encoding="utf-8") as f:
            yield from f
```

## Generator pipelines

Small generators chain into a **pipeline**: each stage pulls items from the previous one, one at a time. Only one item is in flight at any moment, so memory use stays flat no matter how big the input is.

```python
import json

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")

def non_empty(lines):
    for line in lines:
        if line.strip():
            yield line

def parse_json(lines):
    for line in lines:
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue       # skip bad lines instead of crashing the whole job

def only_errors(records):
    return (r for r in records if r.get("level") == "error")

# Nothing is read until this loop starts pulling items:
# for record in only_errors(parse_json(non_empty(read_lines("app.jsonl")))):
#     print(record["message"])
```

Each stage is small, testable on its own (pass it a list instead of a file), and reusable. This **JSON Lines** format (one JSON object per line, `.jsonl`) is common in AI work: datasets, evaluation results and logs are often stored this way exactly because they can be processed line by line.

> **Try it:** Build a list of strings that imitates a file (`["{\"level\": \"error\", \"message\": \"x\"}", "", "junk"]`) and pass it to `parse_json(non_empty(...))`. Because the stages only need an iterable, a list works just like a file.

## `itertools` basics

The `itertools` module has fast building blocks for iterators. The ones you'll use most:

```python
from itertools import islice, chain, count, batched, groupby

# islice: take a slice of any iterator (like list slicing, but lazy)
print(list(islice(count(start=10), 3)))          # [10, 11, 12]   count() never ends

# chain: one iterator after another
print(list(chain([1, 2], (3, 4))))               # [1, 2, 3, 4]

# batched (3.12+): groups of n, as tuples
print(list(batched("abcdefg", 3)))               # [('a','b','c'), ('d','e','f'), ('g',)]

# groupby: group consecutive items by a key (sort by the same key first)
words = sorted(["apple", "avocado", "banana", "blueberry"], key=lambda w: w[0])
for letter, group in groupby(words, key=lambda w: w[0]):
    print(letter, list(group))
# a ['apple', 'avocado']
# b ['banana', 'blueberry']
```

Batching is a constant in AI pipelines: embedding APIs accept a limited number of texts per request, so you send 100 at a time. `islice` is how you take "the next 100" from an iterator without consuming more:

```python
from itertools import islice

def take(n, iterable):
    return list(islice(iterable, n))

docs = (f"document {i}" for i in range(250))
while batch := take(100, docs):
    print(len(batch))     # 100, 100, 50
```

The `:=` "walrus" operator assigns and tests in one go: the loop stops when `take` returns an empty list.

## Lazy processing of big files

Compare two ways to count error lines in a huge log:

```python
# Loads the whole file into memory first: fails on files bigger than your RAM.
with open("big.log", encoding="utf-8") as f:
    n = sum(1 for line in f.readlines() if "ERROR" in line)

# Streams line by line: constant memory, works on any size.
with open("big.log", encoding="utf-8") as f:
    n = sum(1 for line in f if "ERROR" in line)
```

The difference is `.readlines()`, which builds a list of every line. Iterating the file object directly reads it in chunks behind the scenes. The same goes for `.read()` and `json.load()` on a giant file: they need the whole thing in memory. Prefer line-oriented formats (JSON Lines, CSV) for big data so you can stream them.

## Streaming LLM responses

Here is what streaming looks like with the Claude SDK (you'll run it for real in the next section):

```python
import anthropic

client = anthropic.Anthropic()
with client.messages.stream(
    model="claude-opus-5-5", max_tokens=64000,
    messages=[{"role": "user", "content": "Explain generators in two sentences."}],
) as stream:
    for chunk in stream.text_stream:       # an iterator of text pieces
        print(chunk, end="", flush=True)   # show each piece as it arrives
    final = stream.get_final_message()     # the full message, once done
```

`stream.text_stream` is an iterator: each `next()` waits for the next piece of text from the network. Your `for` loop doesn't know or care that items arrive over several seconds. `flush=True` makes each piece appear immediately instead of waiting for a full line.

Under the hood, the API sends **server-sent events**: lines of text, each describing an event such as "message started", "here's a text delta", "message stopped". The SDK parses those lines into events, filters the text deltas, and yields the text. That's a generator pipeline, the same shape you'll build in the stream exercise:

```python
def text_from_events(events):
    for event in events:
        if event.get("type") == "text_delta":
            yield event["text"]

events = [{"type": "message_start"}, {"type": "text_delta", "text": "Hi "},
          {"type": "text_delta", "text": "there"}, {"type": "message_stop"}]
print("".join(text_from_events(events)))   # Hi there
```

A common pattern is to show chunks as they arrive **and** keep the full text for later (to save to a database or add to the chat history):

```python
parts = []
for chunk in text_from_events(events):
    print(chunk, end="", flush=True)
    parts.append(chunk)
full_text = "".join(parts)
```

Collect pieces in a list and `"".join` them at the end; repeated `s += chunk` on long strings is slower.

## Common mistakes

- **Looping over an iterator twice.** The second loop sees nothing. If you need the data twice, store it in a list (if it fits) or recreate the iterator.
- **Calling `list()` on something huge or infinite.** `list(count())` never returns. Use `islice` to take what you need.
- **Expecting a generator's checks to run on call.** The body runs on the first `next()`. Validate arguments in a wrapper function.
- **Using `.readlines()` or `.read()` on big files.** Iterate the file object instead.
- **Forgetting that `itertools.groupby` only groups neighbours.** Sort by the same key first.
- **Building a stream's text with `+=` in a loop.** Append to a list and join once.

## Recap

- Iterables can be looped over; iterators hand out items one at a time with `next()` and are used up after one pass.
- A function with `yield` is a generator: lazy, pausing at each `yield`, with its state preserved.
- Generator expressions `(x for x in xs)` are lazy comprehensions.
- Chain small generators into pipelines to process unlimited data with constant memory.
- `itertools`: `islice`, `chain`, `count`, `batched`, `groupby`.
- A streamed LLM response is an iterator of chunks: loop over it, print with `flush=True`, collect and join for the full text.
