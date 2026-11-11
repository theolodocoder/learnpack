import os
from collections.abc import Mapping

import httpx

DEFAULT_URL = "https://api.weather.example"


def make_client(env: Mapping[str, str], transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """Build an httpx.Client from WEATHER_API_KEY / WEATHER_API_URL in `env`."""
    # TODO: read and check the key (raise RuntimeError if missing/empty)
    # TODO: read the base URL with a default
    # TODO: return httpx.Client(base_url=..., headers=..., timeout=10.0, transport=transport)
    raise NotImplementedError


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"auth": request.headers.get("authorization")})

    try:
        with make_client({"WEATHER_API_KEY": "demo-key"}, transport=httpx.MockTransport(handler)) as c:
            print(c.get("/today").json())
        make_client(os.environ)  # probably no WEATHER_API_KEY set: see the error message
    except RuntimeError as e:
        print("RuntimeError:", e)
    except NotImplementedError:
        print("Not implemented yet: fill in the TODOs, then Run again.")
