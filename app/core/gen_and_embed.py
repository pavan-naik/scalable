import asyncio
import numpy as np

async def run_generation_task(query: str = "Sample query for generation"):
    # Simulate a heavy process
    response = f"Generated response for query: {query}"
    return response

async def run_embedding_task(text: str = "Sample text for embedding"):
    embedding = np.random.rand(512)
    return embedding.tolist()