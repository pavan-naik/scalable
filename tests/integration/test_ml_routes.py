"""
tests/integration/test_ml_routes.py

Integration tests for /generate and /embed.

IMPORTANT NOTE ON SCHEMAS:
Your routes currently do:
    return GenerationResponse(response=result)   # result is now a dict
    return EmbeddingResponse(embedding=result)   # result is now a dict

This will crash because GenerationResponse.response expects a str,
and EmbeddingResponse.embedding expects a list — but you're passing dicts.

You need to update your schemas and routes. Two options:

Option A — Extract from the dict in the route:
    return GenerationResponse(response=result["choices"][0]["message"]["content"])

Option B — Update schemas to accept the full dict shape:
    class GenerationResponse(BaseModel):
        id: str
        object: str
        model: str
        choices: list

These tests are written assuming Option A (extract in route) because it's
the cleaner API surface for callers. Adjust if you choose Option B.

The integration tests mock run_generation_task / run_embedding_task so they
don't care about HTTP — they only test the route wiring and response shape.
"""

import pytest


class TestGenerateEndpoint:

    # ------------------------------------------------------------------
    # These tests use mock_generation_task fixture from conftest.
    # The fixture intercepts the call at app.routers.ml level.
    # ------------------------------------------------------------------

    def test_returns_200(self, client, mock_generation_task):
        response = client.post("/generate", json={"query": "hello"})
        assert response.status_code == 200

    def test_response_has_response_key(self, client, mock_generation_task):
        response = client.post("/generate", json={"query": "hello"})
        assert "response" in response.json()

    def test_response_value_is_string(self, client, mock_generation_task):
        response = client.post("/generate", json={"query": "hello"})
        assert isinstance(response.json()["response"], str)

    def test_core_function_was_called(self, client, mock_generation_task):
        """
        Verify the route actually called run_generation_task.
        This catches accidental dead code — if the route returns hardcoded
        data without calling the function, the mock's assert_called catches it.
        """
        client.post("/generate", json={"query": "hello"})
        mock_generation_task.assert_called_once()

    def test_core_function_received_correct_query(self, client, mock_generation_task):
        """Verify the route passed the user's query to the core function."""
        client.post("/generate", json={"query": "my specific query"})
        mock_generation_task.assert_called_once_with("my specific query")

    def test_content_type_is_json(self, client, mock_generation_task):
        response = client.post("/generate", json={"query": "hello"})
        assert "application/json" in response.headers["content-type"]

    # ------------------------------------------------------------------
    # Sad path — no mock needed, Pydantic validation fires before
    # the route handler runs, so mock_generation_task is not required
    # ------------------------------------------------------------------

    def test_missing_query_returns_422(self, client):
        response = client.post("/generate", json={})
        assert response.status_code == 422

    def test_null_query_returns_422(self, client):
        response = client.post("/generate", json={"query": None})
        assert response.status_code == 422

    def test_missing_query_uses_standard_error_envelope(self, client):
        response = client.post("/generate", json={})
        body = response.json()
        assert "error" in body
        assert "detail" not in body  # FastAPI's default format — should be overridden

    def test_missing_query_returns_correct_error_code(self, client):
        response = client.post("/generate", json={})
        assert response.json()["error"]["code"] == "VAL_REQUEST_001"

    def test_missing_query_identifies_failing_field(self, client):
        response = client.post("/generate", json={})
        errors = response.json()["error"]["details"]["validation_errors"]
        fields = [e["field"] for e in errors]
        assert "query" in fields

    def test_error_response_has_timestamp(self, client):
        response = client.post("/generate", json={})
        assert "timestamp" in response.json()["error"]

    def test_error_response_has_path(self, client):
        response = client.post("/generate", json={})
        assert response.json()["error"]["path"] == "/generate"

    @pytest.mark.parametrize("query", [
        "hello",
        "unicode: café",
        "a " * 200,
        "newline\nquery",
    ])
    def test_various_queries_return_200(self, client, mock_generation_task, query):
        response = client.post("/generate", json={"query": query})
        assert response.status_code == 200


class TestEmbedEndpoint:

    def test_returns_200(self, client, mock_embedding_task):
        response = client.post("/embed", json={"text": "hello"})
        assert response.status_code == 200

    def test_response_has_embedding_key(self, client, mock_embedding_task):
        response = client.post("/embed", json={"text": "hello"})
        assert "embedding" in response.json()

    def test_embedding_is_a_list(self, client, mock_embedding_task):
        response = client.post("/embed", json={"text": "hello"})
        assert isinstance(response.json()["embedding"], list)

    def test_embedding_has_512_dimensions(self, client, mock_embedding_task):
        response = client.post("/embed", json={"text": "hello"})
        assert len(response.json()["embedding"]) == 512

    def test_core_function_was_called(self, client, mock_embedding_task):
        client.post("/embed", json={"text": "hello"})
        mock_embedding_task.assert_called_once()

    def test_core_function_received_correct_text(self, client, mock_embedding_task):
        client.post("/embed", json={"text": "my specific text"})
        mock_embedding_task.assert_called_once_with("my specific text")

    def test_missing_text_returns_422(self, client):
        response = client.post("/embed", json={})
        assert response.status_code == 422

    def test_missing_text_identifies_failing_field(self, client):
        response = client.post("/embed", json={})
        errors = response.json()["error"]["details"]["validation_errors"]
        fields = [e["field"] for e in errors]
        assert "text" in fields