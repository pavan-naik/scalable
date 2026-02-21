"""
conftest.py

Key change from before: we now have TWO levels of mocking needed.

1. For UNIT tests of gen_and_embed.py:
   Mock httpx.AsyncClient so no real HTTP call is made.

2. For INTEGRATION tests of routes (ml.py):
   Mock run_generation_task / run_embedding_task at app.routers.ml
   (where they're USED, not where they're defined).
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# App / HTTP client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Canonical response shapes
#
# Define the expected shapes ONCE here.
# Tests import these — if the shape changes, you fix it in one place.
# ---------------------------------------------------------------------------

MOCK_GENERATION_RESPONSE = {
    "id": "test-uuid-1234",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "mock-gemma3:4b",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Processed remotely: test query"
            },
            "finish_reason": "stop"
        }
    ]
}

MOCK_EMBEDDING_RESPONSE = {
    "object": "embedding",
    "model": "mock-embeddinggemma",
    "embedding": [0.1] * 512
}


# ---------------------------------------------------------------------------
# httpx mock helpers
#
# Your functions use httpx as an async context manager:
#
#   async with httpx.AsyncClient() as client:
#       response = await client.post(...)
#
# To mock this you need to mock THREE things:
#   1. httpx.AsyncClient() constructor call
#   2. __aenter__ (the `async with` entry — returns the client object)
#   3. __aexit__  (the `async with` exit — cleanup)
#   4. client.post() (the actual call inside the block)
# ---------------------------------------------------------------------------

def _make_mock_client(response: MagicMock) -> AsyncMock:
    """Build a mock httpx.AsyncClient that returns a given response."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=response)
    # async context manager protocol
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


def _make_httpbin_response(echoed_json: dict) -> MagicMock:
    """
    Build a fake httpx.Response that mimics what httpbin.org/post returns.

    httpbin echoes your POST body back under the "json" key:
        POST {"prompt": "hello"}  →  response.json() == {"json": {"prompt": "hello"}, ...}
    """
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()  # no-op — simulates 200 OK
    mock_response.json.return_value = {"json": echoed_json}
    return mock_response


# ---------------------------------------------------------------------------
# Fixtures for unit testing gen_and_embed.py
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_httpx_generation():
    """Mocks httpx for run_generation_task — simulates httpbin echoing the prompt."""
    echoed = {"prompt": "test query", "model": "mock-gemma3:4b"}
    response = _make_httpbin_response(echoed)
    mock_client = _make_mock_client(response)

    with patch("app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_httpx_embedding():
    """Mocks httpx for run_embedding_task — simulates httpbin echoing the input."""
    echoed = {"input": "test text", "model": "mock-embeddinggemma"}
    response = _make_httpbin_response(echoed)
    mock_client = _make_mock_client(response)

    with patch("app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_httpx_server_error():
    """Mocks httpx to simulate a 500 from the upstream server."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Internal Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )
    mock_client = _make_mock_client(mock_response)

    with patch("app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client):
        yield


@pytest.fixture
def mock_httpx_timeout():
    """Mocks httpx to simulate a network timeout."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client):
        yield


# ---------------------------------------------------------------------------
# Fixtures for integration testing routes (ml.py)
#
# These mock at app.routers.ml — where the functions are USED after import.
# The route tests don't care about HTTP at all, only the dict shape.
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_generation_task():
    with patch(
        "app.routers.ml.run_generation_task",
        new_callable=AsyncMock,
        return_value=MOCK_GENERATION_RESPONSE,
    ) as mock:
        yield mock


@pytest.fixture
def mock_embedding_task():
    with patch(
        "app.routers.ml.run_embedding_task",
        new_callable=AsyncMock,
        return_value=MOCK_EMBEDDING_RESPONSE,
    ) as mock:
        yield mock