import asyncio

import httpx
from pydantic import BaseModel, Field, ValidationError


class Post(BaseModel):
    # TODO: id > 0, user_id from "userId" and > 0, title at least 1 char, body
    id: int
    user_id: int
    title: str
    body: str


class Failure(BaseModel):
    url: str
    error: str


async def fetch_one(client: httpx.AsyncClient, url: str) -> Post | Failure:
    """GET url and return a validated Post, or a Failure describing what went wrong."""
    # TODO: try: response = await client.get(url); response.raise_for_status()
    #       except httpx.HTTPStatusError -> Failure(url=url, error=f"HTTP {status}")
    #       except httpx.RequestError as e -> Failure(..., error=f"request failed: {type(e).__name__}")
    # TODO: try: data = response.json()   except ValueError -> "invalid JSON"
    # TODO: try: return Post.model_validate(data)   except ValidationError -> "invalid data: ..."
    raise NotImplementedError


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/posts/1":
            return httpx.Response(200, json={"id": 1, "userId": 7, "title": "Hello", "body": "First post"})
        return httpx.Response(404)

    async def demo():
        async with httpx.AsyncClient(base_url="https://api.example.com",
                                     transport=httpx.MockTransport(handler)) as client:
            print(await fetch_one(client, "/posts/1"))
            print(await fetch_one(client, "/posts/2"))

    try:
        asyncio.run(demo())
    except NotImplementedError:
        print("Not implemented yet: fill in the TODOs, then Run again.")
