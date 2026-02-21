import pytest
from app.core.gen_and_embed import run_generation_task, run_embedding_task


@pytest.mark.asyncio
async def test_run_generation_task_default():
    result = await run_generation_task()
    assert isinstance(result, str)
    assert "Sample query for generation" in result


@pytest.mark.asyncio
async def test_run_generation_task_custom_query():
    query = "What is the capital of France?"
    result = await run_generation_task(query=query)
    assert isinstance(result, str)
    assert query in result


@pytest.mark.asyncio
async def test_run_embedding_task_default():
    result = await run_embedding_task()
    assert isinstance(result, list)
    assert len(result) == 512
    assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_run_embedding_task_custom_text():
    result = await run_embedding_task(text="Hello world")
    assert isinstance(result, list)
    assert len(result) == 512


@pytest.mark.asyncio
async def test_run_embedding_task_values_in_range():
    result = await run_embedding_task()
    assert all(0.0 <= v <= 1.0 for v in result)
