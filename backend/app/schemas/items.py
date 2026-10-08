import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from app.db.models import SourceType


class IngestRequest(BaseModel):
    source_type: SourceType
    content: str | None = Field(default=None, description="Required when source_type is 'note'")
    url: str | None = Field(default=None, description="Required when source_type is 'url'")

    @field_validator("content", "url")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @model_validator(mode="after")
    def validate_payload_matches_type(self) -> "IngestRequest":
        if self.source_type == SourceType.note and not (self.content and self.content.strip()):
            raise ValueError("content is required and cannot be blank when source_type is 'note'")
        if self.source_type == SourceType.url and not (self.url and self.url.strip()):
            raise ValueError("url is required and cannot be blank when source_type is 'url'")
        return self


class ItemResponse(BaseModel):
    id: uuid.UUID
    source_type: SourceType
    source_ref: str | None
    content: str
    suggested_question: str | None
    created_at: datetime
    chunk_count: int

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
