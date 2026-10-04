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
    retries: int = 3,
) -> str:
    """
    Send messages to Groq and return the model response.
    """

    client = create_groq_client()

    last_error = None

    for attempt in range(retries):

        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

            return response.choices[0].message.content

        except Exception as error:
            last_error = error

    raise RuntimeError(
        f"Groq API failed after {retries} attempts: {last_error}"
    )