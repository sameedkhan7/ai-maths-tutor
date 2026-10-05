from typing import Literal

from pydantic import BaseModel, Field


# =========================
# CHAT MESSAGE
# =========================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# =========================
# RAG CHUNK
# =========================

class RAGChunk(BaseModel):
    text: str
    source: str
    page: int
    score: float = Field(ge=0, le=1)


# =========================
# TUTOR REQUEST
# =========================
class TutorRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)
    explanation_style: str = "simple"
    language: Literal["english", "hindi", "hinglish", "urdu"] = "english"
    student_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    rag_chunks: list[RAGChunk] = Field(default_factory=list)
    model: str = "llama-3.3-70b-versatile"

# =========================
# TUTOR RESPONSE
# =========================

class TutorResponse(BaseModel):
    answer: str
    question_type: str
    explanation_style: str
    used_rag: bool
    sources: list[str]
    prompt_version: str
    model: str
    error: str | None = None