import asyncio
import json
from pathlib import Path

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



async def fetch_all(client: httpx.AsyncClient, urls: list[str], limit: int = 5) -> tuple[list[Post], list[Failure]]:
    """Fetch every URL (at most `limit` at once). Return (posts, failures), each in URL order."""
    # TODO: make a Semaphore(limit); define an inner async function that holds it while awaiting fetch_one
    # TODO: gather all of them, then split the results with isinstance(r, Post)
    raise NotImplementedError


def write_report(posts: list[Post], failures: list[Failure], path: str | Path) -> None:
    """Write {"posts": [...], "failures": [...]} as JSON to `path`."""
    # TODO: build the dict with model_dump(), make the parent folder, write json.dumps(..., indent=2)
    raise NotImplementedError


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        n = int(request.url.path.rsplit("/", 1)[-1])
        if n == 3:
            return httpx.Response(404)
        return httpx.Response(200, json={"id": n, "userId": 1, "title": f"Post {n}", "body": "..."})

    async def demo():
        urls = [f"/posts/{n}" for n in range(1, 6)]
        async with httpx.AsyncClient(base_url="https://api.example.com",
                                     transport=httpx.MockTransport(handler)) as client:
            posts, failures = await fetch_all(client, urls, limit=2)
        print(len(posts), "posts,", len(failures), "failures:", failures)
        write_report(posts, failures, "report.json")
        print(Path("report.json").read_text()[:200])

    try:
        asyncio.run(demo())
    except NotImplementedError:
        print("Not implemented yet: fill in the TODOs, then Run again.")
