# Issue and verify hashed API keys

When you give customers API keys, store only a **hash** of each key, the way you'd store passwords. If your database leaks, the attacker gets hashes they can't use.

```python
def generate_api_key(prefix: str = "sk_live") -> str: ...
def hash_api_key(key: str) -> str: ...
def verify_api_key(key: str, stored_hash: str) -> bool: ...
def find_owner(key: str | None, keys_by_hash: dict[str, str]) -> str | None: ...
```

1. **`generate_api_key`** returns `f"{prefix}_{secrets.token_urlsafe(32)}"`: 32 random bytes, so 43 URL-safe characters after the prefix. The prefix lets people (and GitHub's secret scanning) recognise what the string is.
2. **`hash_api_key`** returns `hashlib.sha256(key.encode()).hexdigest()`. A fast hash is fine here because the key is long and random. Passwords chosen by people need a slow hash (bcrypt, scrypt, argon2) instead.
3. **`verify_api_key`** hashes `key` and compares it with `stored_hash` using `hmac.compare_digest`, a constant-time comparison. An empty `key` or empty `stored_hash` always returns `False`.
4. **`find_owner`** looks the key's hash up in a `{hash: owner}` table (your database, in real life). It returns `None` for an unknown, empty or `None` key.

## Example

```python
key = generate_api_key()           # 'sk_live_Jx3...'
stored = hash_api_key(key)         # '9f2c...' (64 hex characters)
verify_api_key(key, stored)        # True
verify_api_key("sk_live_x", stored)  # False
find_owner(key, {stored: "acme"})  # 'acme'
```
