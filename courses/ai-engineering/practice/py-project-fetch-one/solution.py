import asyncio

import httpx
from pydantic import BaseModel, Field, ValidationError


class Post(BaseModel):
    id: int = Field(gt=0)
    user_id: int = Field(alias="userId", gt=0)
    title: str = Field(min_length=1)
    body: str


class Failure(BaseModel):
    url: str
    error: str


async def fetch_one(client: httpx.AsyncClient, url: str) -> Post | Failure:
    """GET url and return a validated Post, or a Failure describing what went wrong."""
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return Failure(url=url, error=f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        return Failure(url=url, error=f"request failed: {type(e).__name__}")

    try:
        data = response.json()
    except ValueError:
        return Failure(url=url, error="invalid JSON")

    try:
        return Post.model_validate(data)
    except ValidationError as e:
        details = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
        return Failure(url=url, error=f"invalid data: {details}")


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

    asyncio.run(demo())
