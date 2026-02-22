import httpx
import uuid
import time
import numpy as np

HTTPBIN_URL = "https://httpbin.org/post"


async def run_generation_task(query: str):
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            HTTPBIN_URL, json={"model": "mock-gemma3:4b", "prompt": query}
        )
    response.raise_for_status()
    data = response.json()

    # httpbin echoes your JSON under "json"
    answer = data["json"]["prompt"]

    # Build realistic LLM-shaped output
    return {
        "id": str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "mock-gemma3:4b",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Processed remotely: {answer}",
                },
                "finish_reason": "stop",
            }
        ],
    }


async def run_embedding_task(text: str):
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            HTTPBIN_URL, json={"model": "mock-embeddinggemma", "input": text}
        )

    response.raise_for_status()
    data = response.json()

    echoed_text = data["json"]["input"]

    # Generate deterministic fake embedding from text length
    np.random.seed(len(echoed_text))
    embedding = np.random.rand(512).tolist()

    return {
        "object": "embedding",
        "model": "mock-embeddinggemma",
        "embedding": embedding,
    }
