# Summarise old turns, keep recent ones

Dropping old turns (as in *How LLMs work*) loses facts the user told you an hour ago. A better trade: **summarise** the old turns with a cheap model and keep the newest turns word for word.

```python
def compact_history(client, messages: list[dict], keep_last: int = 4,
                    model: str = "claude-haiku-5-5") -> list[dict]: ...
```

Every message is `{"role": "user" | "assistant", "content": str}`.

1. If there are `keep_last` messages or fewer, return a copy of the list unchanged, **without** calling the API.
2. Split into `old = messages[:-keep_last]` and `recent = messages[-keep_last:]`. The API needs the first message to be from the user, so while `recent` starts with an `assistant` message, move the boundary back one (keep one more message in `recent`). If that empties `old`, return a copy unchanged with no call.
3. Build a transcript of `old`, one line per message: `"user: ..."` / `"assistant: ..."`. Call `client.messages.create(model=model, max_tokens=..., system=..., messages=[...])` with that transcript inside `<transcript>...</transcript>` tags, asking for a summary that keeps names, numbers, decisions and open questions.
4. Return `recent`, but with the summary prepended to the **first** recent message's content:
   ```python
   f"<summary>\n{summary}\n</summary>\n\n{original content}"
   ```
   Don't modify the input list or its dicts.

## Example

```python
msgs = [u("My name is Ada"), a("Hi Ada"), u("I use Postgres 16"), a("Noted"),
        u("Why is my query slow?"), a("Can you share it?"), u("SELECT ...")]
compact_history(client, msgs, keep_last=3)
# old = first 4 messages -> summarised: "User is Ada, uses Postgres 16."
# -> [{"role": "user", "content": "<summary>\nUser is Ada, uses Postgres 16.\n</summary>\n\nWhy is my query slow?"},
#     {"role": "assistant", "content": "Can you share it?"},
#     {"role": "user", "content": "SELECT ..."}]
```

**Check is free and offline.** **Run** uses the real API if your key is set.
