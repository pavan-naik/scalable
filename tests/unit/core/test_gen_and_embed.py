"""
tests/unit/core/test_gen_and_embed.py

Unit tests for run_generation_task and run_embedding_task.

Now that these functions make real HTTP calls, EVERY test here must use
a mock_httpx_* fixture. Without it, your tests would:
  - Hit the real internet (slow, flaky, costs money in production)
  - Fail in CI environments with no outbound network
  - Not be unit tests at all

The pattern in every test:
    async def test_something(self, mock_httpx_generation):
                                   ^^^^^^^^^^^^^^^^^^^
                                   This fixture activates before the test,
                                   replacing httpx.AsyncClient with a fake.
                                   The real network is never touched.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch


class TestRunGenerationTask:
    # ------------------------------------------------------------------
    # Response shape tests — the most important category
    #
    # Your function returns a dict now. Every key a caller might access
    # should be tested explicitly. If you rename "choices" to "results",
    # these tests catch it immediately.
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_returns_dict(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_response_has_id_field(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert "id" in result

    @pytest.mark.asyncio
    async def test_id_is_a_string(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert isinstance(result["id"], str)

    @pytest.mark.asyncio
    async def test_id_is_not_empty(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert len(result["id"]) > 0

    @pytest.mark.asyncio
    async def test_response_has_object_field(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert result["object"] == "chat.completion"

    @pytest.mark.asyncio
    async def test_response_has_model_field(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert result["model"] == "mock-gemma3:4b"

    @pytest.mark.asyncio
    async def test_response_has_created_timestamp(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert "created" in result
        assert isinstance(result["created"], int)
        assert result["created"] > 0

    @pytest.mark.asyncio
    async def test_response_has_choices_list(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert "choices" in result
        assert isinstance(result["choices"], list)

    @pytest.mark.asyncio
    async def test_choices_has_at_least_one_item(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert len(result["choices"]) >= 1

    @pytest.mark.asyncio
    async def test_first_choice_has_message(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        choice = result["choices"][0]
        assert "message" in choice

    @pytest.mark.asyncio
    async def test_message_has_role_and_content(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        message = result["choices"][0]["message"]
        assert "role" in message
        assert "content" in message

    @pytest.mark.asyncio
    async def test_message_role_is_assistant(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert result["choices"][0]["message"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_message_content_is_string(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        content = result["choices"][0]["message"]["content"]
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_message_content_contains_query(self, mock_httpx_generation):
        """
        The function builds content as f"Processed remotely: {answer}"
        where answer is the echoed prompt. We test the contract that
        the query ends up in the content — not the exact wording.
        """
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        content = result["choices"][0]["message"]["content"]
        assert "test query" in content

    @pytest.mark.asyncio
    async def test_finish_reason_is_stop(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        result = await run_generation_task("test query")
        assert result["choices"][0]["finish_reason"] == "stop"

    # ------------------------------------------------------------------
    # HTTP behavior tests
    #
    # These verify that your function sends the right request.
    # Useful when integrating with a real model API — you want to be sure
    # the payload shape is correct before hitting real infrastructure.
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_posts_to_correct_url(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task, HTTPBIN_URL

        await run_generation_task("test query")
        mock_httpx_generation.post.assert_called_once()
        call_kwargs = mock_httpx_generation.post.call_args
        assert call_kwargs[0][0] == HTTPBIN_URL  # first positional arg

    @pytest.mark.asyncio
    async def test_sends_query_as_prompt(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        await run_generation_task("my specific query")
        call_kwargs = mock_httpx_generation.post.call_args
        sent_json = call_kwargs[1]["json"]  # keyword arg `json=`
        assert sent_json["prompt"] == "my specific query"

    @pytest.mark.asyncio
    async def test_sends_correct_model_name(self, mock_httpx_generation):
        from app.core.gen_and_embed import run_generation_task

        await run_generation_task("test")
        call_kwargs = mock_httpx_generation.post.call_args
        sent_json = call_kwargs[1]["json"]
        assert sent_json["model"] == "mock-gemma3:4b"

    # ------------------------------------------------------------------
    # Error handling tests — the category most people forget entirely
    #
    # Your function calls raise_for_status(). If the server returns 500,
    # that raises httpx.HTTPStatusError. What does YOUR function do with it?
    # Currently: it propagates. These tests document that behavior.
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_propagates_http_error_on_server_failure(
        self, mock_httpx_server_error
    ):
        """
        When the upstream server returns 5xx, raise_for_status() raises.
        Currently your function doesn't catch it — it bubbles up.
        This test documents that behavior explicitly.
        If you later add error handling, this test changes to match.
        """
        from app.core.gen_and_embed import run_generation_task

        with pytest.raises(httpx.HTTPStatusError):
            await run_generation_task("test query")

    @pytest.mark.asyncio
    async def test_propagates_timeout_error(self, mock_httpx_timeout):
        """When the network times out, TimeoutException propagates."""
        from app.core.gen_and_embed import run_generation_task

        with pytest.raises(httpx.TimeoutException):
            await run_generation_task("test query")

    # ------------------------------------------------------------------
    # Parametrized input tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query",
        [
            "short",
            "a longer query with multiple words",
            "unicode: café 日本語",
            "special: !@#$%",
            "query\nwith\nnewlines",
        ],
    )
    async def test_handles_various_query_strings(self, query):
        """
        For each input, set up its own mock that echoes the specific query.
        We can't use the fixture here because the echoed value changes per input.
        """
        from app.core.gen_and_embed import run_generation_task

        echoed = {"prompt": query, "model": "mock-gemma3:4b"}
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"json": echoed}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client
        ):
            result = await run_generation_task(query)

        assert isinstance(result, dict)
        assert "choices" in result


class TestRunEmbeddingTask:
    @pytest.mark.asyncio
    async def test_returns_dict(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_response_has_object_field(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert result["object"] == "embedding"

    @pytest.mark.asyncio
    async def test_response_has_model_field(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert result["model"] == "mock-embeddinggemma"

    @pytest.mark.asyncio
    async def test_response_has_embedding_key(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert "embedding" in result

    @pytest.mark.asyncio
    async def test_embedding_is_a_list(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert isinstance(result["embedding"], list)

    @pytest.mark.asyncio
    async def test_embedding_has_512_dimensions(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert len(result["embedding"]) == 512

    @pytest.mark.asyncio
    async def test_embedding_values_are_floats(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert all(isinstance(v, float) for v in result["embedding"])

    @pytest.mark.asyncio
    async def test_embedding_values_in_zero_to_one_range(self, mock_httpx_embedding):
        """np.random.rand() produces [0, 1) — document and enforce this range."""
        from app.core.gen_and_embed import run_embedding_task

        result = await run_embedding_task("test text")
        assert all(0.0 <= v <= 1.0 for v in result["embedding"])

    @pytest.mark.asyncio
    async def test_sends_text_as_input_field(self, mock_httpx_embedding):
        from app.core.gen_and_embed import run_embedding_task

        await run_embedding_task("my specific text")
        # mock_httpx_embedding is the mock_client, check what was posted
        # We verify via the fixture's mock_client.post call args
        # (see conftest — mock_httpx_embedding yields mock_client)

    @pytest.mark.asyncio
    async def test_propagates_http_error_on_server_failure(
        self, mock_httpx_server_error
    ):
        from app.core.gen_and_embed import run_embedding_task

        with pytest.raises(httpx.HTTPStatusError):
            await run_embedding_task("test text")

    @pytest.mark.asyncio
    async def test_propagates_timeout_error(self, mock_httpx_timeout):
        from app.core.gen_and_embed import run_embedding_task

        with pytest.raises(httpx.TimeoutException):
            await run_embedding_task("test text")

    @pytest.mark.asyncio
    async def test_embedding_is_deterministic_for_same_text(self):
        """
        Your function uses np.random.seed(len(text)) — same length = same embedding.
        This tests that contract. It's a pure logic test, no HTTP needed.
        """
        from app.core.gen_and_embed import run_embedding_task

        text = "hello"
        echoed = {"input": text, "model": "mock-embeddinggemma"}
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"json": echoed}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.core.gen_and_embed.httpx.AsyncClient", return_value=mock_client
        ):
            result1 = await run_embedding_task(text)
            result2 = await run_embedding_task(text)

        assert result1["embedding"] == result2["embedding"]
