from groq import Groq

from backend.ai.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    TEMPERATURE,
    MAX_TOKENS,
)


def create_groq_client() -> Groq:
    """
    Create and return Groq API client.
    """

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing")

    return Groq(api_key=GROQ_API_KEY)


def call_groq(
    messages: list[dict],
    model: str | None = None,
    retries: int = 3,
) -> str:
    """
    Send messages to Groq and return the model response.
    """

    client = create_groq_client()
    default_model = GROQ_MODEL or "openai/gpt-oss-120b"
    target_model = model or default_model

    last_error = None

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

            return response.choices[0].message.content

        except Exception as error:
            last_error = error
            # If model is not found, fallback to the working default model
            if "model_not_found" in str(error) and target_model != default_model:
                target_model = default_model
                continue

    raise RuntimeError(
        f"Groq API failed after {retries} attempts: {last_error}"
    )