from backend.ai.config import (
    GROQ_MODEL,
    PROMPT_VERSION,
)

from backend.ai.schemas import TutorRequest, TutorResponse
from backend.ai.styles import detect_style
from backend.ai.intent import detect_question_type
from backend.ai.prompts import MASTER_SYSTEM_PROMPT
from backend.ai.context_builder import build_messages
from backend.ai.groq_client import call_groq


def generate_tutor_response(req: TutorRequest) -> TutorResponse:
    """
    Main function for generating an AI Maths Tutor response.

    This function never raises an exception.
    Errors are returned inside TutorResponse.error.
    """

    try:
        # Detect question type
        question_type = detect_question_type(req.question)

        # Validate / normalize explanation style
        explanation_style = detect_style(
        req.question,
        req.explanation_style
)

        # Add style and question type information to system prompt
        system_prompt = (
    f"{MASTER_SYSTEM_PROMPT}\n\n"
    f"CURRENT QUESTION TYPE: {question_type}\n"
    f"EXPLANATION STYLE: {explanation_style}\n"
    f"STUDENT LEVEL: {req.student_level}\n"
    f"IMPORTANT: Your entire response MUST be written in {req.language}. "
    f"Do not answer in English unless the requested language is english.\n"
    f"RESPONSE LANGUAGE: {req.language}"
)

        # Build final messages
        messages, sources, used_rag = build_messages(
            req=req,
            system_prompt=system_prompt,
        )

        # Call Groq with selected model
        answer = call_groq(messages, model=req.model)

        return TutorResponse(
            answer=answer,
            question_type=question_type,
            explanation_style=explanation_style,
            used_rag=used_rag,
            sources=sources,
            prompt_version=PROMPT_VERSION,
            model=req.model or GROQ_MODEL or "llama-3.3-70b-versatile",
            error=None,
        )

    except Exception as error:

        return TutorResponse(
            answer="Sorry, I could not generate the answer right now.",
            question_type=detect_question_type(req.question),
            explanation_style=detect_style(req.explanation_style),
            used_rag=False,
            sources=[],
            prompt_version=PROMPT_VERSION,
            model=GROQ_MODEL,
            error=str(error),
        )