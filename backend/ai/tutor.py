from backend.ai.config import (
    GROQ_MODEL,
    PROMPT_VERSION,
)

from backend.ai.schemas import TutorRequest, TutorResponse, RAGChunk
from backend.ai.styles import detect_style
from backend.ai.intent import detect_question_type
from backend.ai.prompts import MASTER_SYSTEM_PROMPT
from backend.ai.context_builder import build_messages
from backend.ai.groq_client import call_groq
from backend.ai.math_engine import get_exact_math_context
from backend.rag.retriever import retrieve_math_context

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

        # 📚 Member 2: Auto-retrieve NCERT RAG chunks from Knowledge Base
        if not req.rag_chunks:
            try:
                rag_res = retrieve_math_context(req.question, top_k=2)
                if rag_res and rag_res.get("has_context"):
                    for c in rag_res.get("chunks", []):
                        req.rag_chunks.append(RAGChunk(
                            text=c["text"],
                            source=c.get("source", "NCERT Mathematics"),
                            page=c.get("page", 1),
                            score=c.get("score", 0.8)
                        ))
            except Exception as e:
                print(f"RAG retrieval notice: {e}")

        # Define explicit language instructions
        lang_str = (req.language or "hinglish").lower()
        if lang_str == "hinglish":
            lang_rule = (
                "RESPONSE LANGUAGE: Hinglish (Conversational Mix of Hindi in Roman script + English math terms). "
                "Write in friendly Indian Hinglish (e.g., 'Samajhte hain ki derivative dy/dx kya hota hai. Rate of change ka matlab...')."
            )
        elif lang_str in ["hi", "hindi"]:
            lang_rule = "RESPONSE LANGUAGE: Hindi (Devanagari script). Write explanations in simple, clear Hindi (हिंदी भाषा)."
        elif lang_str in ["ur", "urdu"]:
            lang_rule = "RESPONSE LANGUAGE: Urdu. Write explanations in clear Urdu script (اردو)."
        elif lang_str in ["ar", "arabic"]:
            lang_rule = "RESPONSE LANGUAGE: Arabic. Write explanations in clear Arabic script (العربية)."
        else:
            lang_rule = f"RESPONSE LANGUAGE: {req.language}. Write explanations in clear, encouraging English."

        # Add style, question type, and typo/formatting instructions to system prompt
        system_prompt = (
            f"{MASTER_SYSTEM_PROMPT}\n\n"
            f"CURRENT QUESTION TYPE: {question_type}\n"
            f"EXPLANATION STYLE: {explanation_style}\n"
            f"STUDENT LEVEL: {req.student_level}\n"
            f"{lang_rule}\n\n"
            f"IMPORTANT RESPONSE RULES:\n"
            f"1. TYPO HANDLING: If the question has a typo or misspelled math term (e.g., 'trignometer', 'tignometer', 'intgration'), DO NOT reject it and DO NOT ask confusing non-math questions like 'did you mean tachometer?'. Gently note the correct spelling in the first line (e.g., '**Trignometer (usually called *trigonometry*)**...') and immediately give the full explanation!\n"
            f"2. FORMATTING: Use clean Markdown headers (### What it does, ### Core Formulas, ### Why it's useful, ### Simple Example, ---, Summary). Use fenced code blocks (```text ... ```) for fraction ratios or ASCII diagrams so formulas stay perfectly aligned.\n"
            f"3. DIAGRAMS: If asked 'with diagram' or for geometry/trigonometry, ALWAYS draw a clear ASCII text diagram inside a fenced code block followed by a Markdown table explaining each part."
        )

        # Check exact mathematical verification with SymPy
        exact_math = get_exact_math_context(req.question)
        if exact_math:
            system_prompt += f"\n\nEXACT MATHEMATICAL VERIFICATION:\n{exact_math}\nUse this exact verified analytical solution in your 5-step intuitive explanation."

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