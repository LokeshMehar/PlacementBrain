from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SourceType(str, Enum):
    pdf = "pdf"
    excel = "excel"
    code = "code"
    markdown = "markdown"
    text = "text"
    repo = "repo"
    jd = "jd"


class IngestResponse(BaseModel):
    source_id: str
    filename: str
    source_type: SourceType
    chunk_count: int
    status: str


class SourceItem(BaseModel):
    source_id: str
    filename: str
    source_type: SourceType
    chunk_count: int
    created_at: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    source_type_filter: Optional[list[SourceType]] = None


class TokenEvent(BaseModel):
    token: str


class DoneEvent(BaseModel):
    sources: list[dict]


class DeleteResponse(BaseModel):
    success: bool
    message: str
