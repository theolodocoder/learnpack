# Route a request to a specialist

Routing sends each input to the prompt (or model) best suited to it. A cheap, fast model classifies; a specialist prompt answers. Write:

```python
ROUTES = {"billing": "...", "technical": "...", "general": "..."}  # given in the starter

def route(client, message: str, router_model: str = "claude-haiku-5-5",
          model: str = "claude-opus-5-5") -> tuple[str, str]: ...
```

1. **Classify:** call `client.messages.create(model=router_model, ...)`. The system prompt lists the three categories and asks for the answer inside `<category>...</category>` tags. The user message contains the customer's message inside `<message>...</message>` tags.
2. Take the text between `<category>` and `</category>`, strip it and lowercase it. If there are no tags, or the result isn't a key of `ROUTES`, use `"general"`. Never let a bad classification crash the request.
3. **Answer:** make a second call with `model=model`, `system=ROUTES[category]`, and `messages=[{"role": "user", "content": message}]`.
4. Return `(category, answer_text)`.

## Example

```python
route(client, "I was charged twice this month")
# call 1 (Haiku) reply: "<category>Billing</category>"
# call 2 (Opus, system=ROUTES["billing"]) reply: "Sorry about that. I've..."
# -> ("billing", "Sorry about that. I've...")
```

**Check is free and offline.** **Run** uses the real API if your key is set.
