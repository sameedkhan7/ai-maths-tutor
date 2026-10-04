from backend.ai.config import (
    MAX_HISTORY_MESSAGES,
    MAX_HISTORY_CHARS,
    MAX_RAG_CHUNKS,
    RAG_MIN_SCORE,
)

from backend.ai.schemas import TutorRequest


# =========================
# HISTORY
# =========================

def build_history(req: TutorRequest) -> list[dict]:
    """
    Keep only the latest allowed chat messages
    within the character limit.
    """

    history = req.chat_history[-MAX_HISTORY_MESSAGES:]

    result = []
    total_chars = 0

    # Newest messages ko priority do
    for message in reversed(history):

        message_chars = len(message.content)

        if total_chars + message_chars > MAX_HISTORY_CHARS:
            break

        result.append({
            "role": message.role,
            "content": message.content,
        })

        total_chars += message_chars

    # Original conversation order restore karo
    result.reverse()

    return result


# =========================
# RAG CONTEXT
# =========================

def build_rag_context(req: TutorRequest) -> tuple[str, list[str]]:
    """
    Filter RAG chunks by score and keep at most
    the configured maximum number of chunks.
    """

    useful_chunks = [
        chunk
        for chunk in req.rag_chunks
        if chunk.score >= RAG_MIN_SCORE
    ]

    # Highest score first
    useful_chunks.sort(
        key=lambda chunk: chunk.score,
        reverse=True
    )

    # Maximum 4 chunks
    useful_chunks = useful_chunks[:MAX_RAG_CHUNKS]

    if not useful_chunks:
        return "", []

    context_parts = []
    sources = []

    for chunk in useful_chunks:

        context_parts.append(
            f"Source: {chunk.source}\n"
            f"Page: {chunk.page}\n"
            f"Content: {chunk.text}"
        )

        sources.append(chunk.source)

    rag_context = "\n\n---\n\n".join(context_parts)

    return rag_context, sources


# =========================
# GROQ MESSAGES
# =========================

def build_messages(
    req: TutorRequest,
    system_prompt: str,
) -> tuple[list[dict], list[str], bool]:
    """
    Build messages that will later be sent to Groq.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Previous conversation
    messages.extend(build_history(req))

    # RAG context
    rag_context, sources = build_rag_context(req)

    # Current question
    user_content = (
        "Use the previous conversation to understand references "
        "such as 'it', 'this', 'that', 'again', or 'why'.\n\n"
    )

    if rag_context:
        user_content += (
            "REFERENCE CONTEXT:\n"
            f"{rag_context}\n\n"
        )

    user_content += (
        "STUDENT QUESTION:\n"
        f"{req.question}"
    )

    messages.append({
        "role": "user",
        "content": user_content,
    })

    return messages, sources, bool(rag_context)