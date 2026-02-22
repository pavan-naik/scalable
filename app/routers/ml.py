from fastapi import APIRouter

from app.core.gen_and_embed import run_generation_task, run_embedding_task
from app.routers.schemas import (
    GenerateParams,
    GenerationResponse,
    EmbeddingResponse,
    EmbeddingParams,
)

router = APIRouter(tags=["ML Operations"])


@router.post("/generate")
async def generate(request: GenerateParams) -> GenerationResponse:
    result = await run_generation_task(request.query)
    return GenerationResponse(response=result["choices"][0]["message"]["content"])


@router.post("/embed")
async def embed(request: EmbeddingParams) -> EmbeddingResponse:
    # Call the core logic
    result = await run_embedding_task(request.text)
    return EmbeddingResponse(embedding=result["embedding"])
