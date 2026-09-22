from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="File name, e.g. notes.md")
    content: str = Field(default="", description="Raw markdown content")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        if not v.lower().endswith(".md"):
            v += ".md"
        return v


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    content: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        if not v.lower().endswith(".md"):
            v += ".md"
        return v


class DocumentOut(BaseModel):
    id: str = Field(validation_alias="_id")
    name: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class DocumentSummary(BaseModel):
    id: str = Field(validation_alias="_id")
    name: str
    created_at: datetime
    updated_at: datetime
    chars: int
    words: int

    model_config = {"populate_by_name": True}
