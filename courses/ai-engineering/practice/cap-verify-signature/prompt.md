# Verify a webhook signature

Anyone on the internet can POST to your webhook URL. WhatsApp (Meta) proves a request is genuine by signing the raw body with your **app secret** and sending the result in a header:

```
X-Hub-Signature-256: sha256=<hex HMAC-SHA256 of the raw body, keyed with the app secret>
```

Write two functions:

```python
def sign(body: bytes, secret: str) -> str:
def verify_signature(body: bytes, header: str | None, secret: str) -> bool:
```

1. **`sign`** returns `"sha256="` followed by the lowercase hex HMAC-SHA256 of `body`, using `secret` (encoded as UTF-8) as the key. Use the `hmac` and `hashlib` modules.
2. **`verify_signature`** returns `True` only if `header` is exactly what `sign(body, secret)` would produce.
   - A missing header (`None`), an empty one or one without the `sha256=` prefix → `False`.
   - Compare with **`hmac.compare_digest`**, not `==`. `==` stops at the first wrong character, so the time it takes leaks how much of a guess was right; `compare_digest` takes the same time either way.

Sign the **raw bytes** you received. If you parse the JSON and re-serialise it, spacing and key order can change and the signature won't match.

## Example

```python
body = b'{"object":"whatsapp_business_account","entry":[]}'
header = sign(body, "app-secret")              # 'sha256=…64 hex chars…'
verify_signature(body, header, "app-secret")   # True
verify_signature(body + b" ", header, "app-secret")  # False: body was changed
verify_signature(body, header, "other-secret")       # False
verify_signature(body, None, "app-secret")           # False
```
