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
    primary_model = model or default_model
    
    # Cascade candidate models if primary hits rate limit (TPD / TPM 429)
    candidate_models = [primary_model]
    for fallback in ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = None

    import time
    for candidate in candidate_models:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=candidate,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
                return response.choices[0].message.content
            except Exception as error:
                last_error = error
                err_str = str(error).lower()
                # If daily quota limit exceeded (TPD), immediately switch to next fallback model
                if "tokens per day" in err_str or "tpd" in err_str:
                    break
                # If short-term minute rate limit (TPM), pause briefly for sub-second reset
                if "tokens per minute" in err_str or "tpm" in err_str:
                    time.sleep(1.5)
                    continue
                if "rate_limit" in err_str or "429" in err_str:
                    break  # switch to next candidate model
                if "model_not_found" in err_str:
                    break  # switch to next candidate model if model name is invalid

    raise RuntimeError(
        f"Groq API failed after trying models {candidate_models}: {last_error}"
    )