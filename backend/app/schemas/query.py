import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceSnippet(BaseModel):
    item_id: uuid.UUID
    source_type: str
    source_ref: str | None
    chunk_text: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]
