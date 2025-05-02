from uuid import UUID

from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    query: str = Field(
        ...,
        description="User's query",
        examples=["Hello! Recommend me a movie about time travel."],
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class DocumentModel(BaseModel):
    page_content: str
    metadata: dict


class ModelResponse(BaseModel):
    input: str
    context: list[DocumentModel] | None
    answer: str


class ChatAnswer(BaseModel):
    user_id: UUID = Field(..., description="User ID")
    generated: ModelResponse


class ChatSession(BaseModel):
    session_id: UUID = Field(..., description="Session ID")
    latest_query: str = Field(..., description="Latest user query")


class ChatHistory(BaseModel):
    history: list[ChatSession] | None
