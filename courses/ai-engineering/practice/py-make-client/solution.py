import os
from collections.abc import Mapping

import httpx

DEFAULT_URL = "https://api.weather.example"


def make_client(env: Mapping[str, str], transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """Build an httpx.Client from WEATHER_API_KEY / WEATHER_API_URL in `env`."""
    key = env.get("WEATHER_API_KEY")
    if not key:
        raise RuntimeError("WEATHER_API_KEY is not set; add it to your .env file")
    base_url = env.get("WEATHER_API_URL", DEFAULT_URL)
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {key}"},
        timeout=10.0,
        transport=transport,
    )


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"auth": request.headers.get("authorization")})

    try:
        with make_client({"WEATHER_API_KEY": "demo-key"}, transport=httpx.MockTransport(handler)) as c:
            print(c.get("/today").json())
        make_client(os.environ)  # probably no WEATHER_API_KEY set: see the error message
    except RuntimeError as e:
        print("RuntimeError:", e)
