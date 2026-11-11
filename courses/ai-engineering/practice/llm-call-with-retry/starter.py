import random
import time


def is_retryable(error: Exception) -> bool:
    """True for 429 and 5xx errors."""
    # TODO: use getattr(error, "status_code", None)
    raise NotImplementedError


def call_with_retry(client, request: dict, max_retries: int = 3,
                    base_delay: float = 1.0, sleep=time.sleep):
    """client.messages.create(**request), retrying 429/5xx with exponential backoff and jitter."""
    # TODO: loop over attempts 0..max_retries
    # TODO:   try: return client.messages.create(**request)
    # TODO:   except Exception as e: re-raise if not retryable or out of retries
    # TODO:   otherwise sleep(base_delay * 2**attempt + random.uniform(0, base_delay * 2**attempt))
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    request = {"model": "claude-haiku-5-5", "max_tokens": 200,
               "messages": [{"role": "user", "content": "Say hi in one word."}]}
    try:
        # max_retries=0 on the client turns off the SDK's own retries so you can see yours work
        response = call_with_retry(anthropic.Anthropic(max_retries=0), request)
        print(response.content[0].text)
    except NotImplementedError:
        print("Write call_with_retry first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
