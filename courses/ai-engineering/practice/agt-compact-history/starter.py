def compact_history(client, messages: list[dict], keep_last: int = 4,
                    model: str = "claude-haiku-5-5") -> list[dict]:
    """Replace all but the newest turns with a summary, folded into the first kept user message."""
    # TODO: short history -> return a copy, no API call
    # TODO: split = len(messages) - keep_last; while messages[split] is an assistant message, split -= 1
    # TODO: if split <= 0: return a copy, no API call
    # TODO: transcript = "\n".join(f"{m['role']}: {m['content']}" for m in old)
    # TODO: summarise it with one call (transcript inside <transcript> tags)
    # TODO: return recent with "<summary>\n...\n</summary>\n\n" prepended to the first message's content
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    def u(t): return {"role": "user", "content": t}
    def a(t): return {"role": "assistant", "content": t}

    history = [u("My name is Ada and I run a bakery in Lagos."), a("Nice to meet you, Ada!"),
               u("I sell about 300 loaves a day."), a("That's a busy bakery."),
               u("How should I price a new sourdough?"), a("What do your ingredients cost per loaf?"),
               u("About ₦900.")]
    try:
        for m in compact_history(anthropic.Anthropic(), history, keep_last=3):
            print(m["role"], "→", m["content"], "\n")
    except NotImplementedError:
        print("Write compact_history first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
