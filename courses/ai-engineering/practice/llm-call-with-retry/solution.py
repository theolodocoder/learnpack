import random
import time


def is_retryable(error: Exception) -> bool:
    """True for 429 and 5xx errors."""
    status = getattr(error, "status_code", None)
    return status is not None and (status == 429 or status >= 500)


def call_with_retry(client, request: dict, max_retries: int = 3,
                    base_delay: float = 1.0, sleep=time.sleep):
    """client.messages.create(**request), retrying 429/5xx with exponential backoff and jitter."""
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**request)
        except Exception as e:
            if not is_retryable(e) or attempt == max_retries:
                raise
            delay = base_delay * 2**attempt
            sleep(delay + random.uniform(0, delay))
