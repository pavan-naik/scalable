from pydantic import BaseModel, Field


class GenerateParams(BaseModel):
    query: str = Field(..., description="The search query string.")

class EmbeddingParams(BaseModel):
    text: str = Field(..., description="The text to be embedded.")


class GenerationResponse(BaseModel):
    response: str = Field(..., description="The generated response based on the query.")

class EmbeddingResponse(BaseModel):
    embedding: list = Field(..., description="The generated embedding vector for the input text.")