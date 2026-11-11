import httpx


def get_json(client: httpx.Client, path: str, params: dict | None = None) -> dict:
    """GET `path` with query `params`; raise on 4xx/5xx; return the JSON body."""
    response = client.get(path, params=params)
    response.raise_for_status()
    return response.json()


def get_user_or_none(client: httpx.Client, user_id: int) -> dict | None:
    """Return the user, or None if the API answers 404. Other errors propagate."""
    try:
        return get_json(client, f"/users/{user_id}")
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            return None
        raise


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/1":
            return httpx.Response(200, json={"id": 1, "name": "Ada"})
        return httpx.Response(404, json={"error": "not found"})

    with httpx.Client(base_url="https://api.example.com", transport=httpx.MockTransport(handler)) as client:
        print(get_user_or_none(client, 1))
        print(get_user_or_none(client, 999))
