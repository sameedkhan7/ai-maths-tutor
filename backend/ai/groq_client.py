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
    Send messages to Groq and return the model response with cascade fallback and retry logic.
    """
    import logging
    import time

    logger = logging.getLogger("groq_client")
    client = create_groq_client()
    default_model = GROQ_MODEL or "openai/gpt-oss-120b"
    primary_model = model or default_model

    # Verified active Groq models for reliable fallback cascade
    verified_fallbacks = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    candidate_models = [primary_model]
    for fb in verified_fallbacks:
        if fb not in candidate_models:
            candidate_models.append(fb)

    last_error = None

    for candidate in candidate_models:
        for attempt in range(retries):
            try:
                logger.info(f"[Groq] Calling model={candidate} (attempt {attempt + 1}/{retries})")
                response = client.chat.completions.create(
                    model=candidate,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
                choice = response.choices[0]
                content = choice.message.content

                # For reasoning models, if content is empty but reasoning is present, handle gracefully
                if not content or not content.strip():
                    reasoning = getattr(choice.message, "reasoning", None)
                    if reasoning and reasoning.strip():
                        # If reasoning completed but content truncated, use reasoning summary or retry with direct model
                        logger.warning(f"[Groq] Model {candidate} returned empty content with reasoning tokens. Falling over to direct text model.")
                        break

                if content and content.strip():
                    return content

                logger.warning(f"[Groq] Model {candidate} returned empty response on attempt {attempt + 1}")

            except Exception as error:
                last_error = error
                err_str = str(error).lower()
                logger.warning(f"[Groq] Error on {candidate} attempt {attempt + 1}: {type(error).__name__} - {err_str[:120]}")

                # If daily quota limit exceeded (TPD), immediately switch to next fallback model
                if "tokens per day" in err_str or "tpd" in err_str:
                    logger.info(f"[Groq] Daily quota limit for {candidate}. Switching to fallback model.")
                    break

                # If short-term minute rate limit (TPM) or 429, pause with exponential backoff
                if "tokens per minute" in err_str or "tpm" in err_str or "429" in err_str or "rate_limit" in err_str:
                    backoff = min(1.5 * (2 ** attempt), 6.0)
                    logger.info(f"[Groq] Rate limit reached. Backing off for {backoff:.1f}s before retry.")
                    time.sleep(backoff)
                    continue

                # Temporary server errors (500, 503)
                if "500" in err_str or "503" in err_str or "internal server error" in err_str or "service unavailable" in err_str:
                    backoff = 1.0 * (attempt + 1)
                    time.sleep(backoff)
                    continue

                # If model not found or invalid model ID, switch to next candidate model immediately
                if "model_not_found" in err_str or "invalid_request_error" in err_str:
                    logger.info(f"[Groq] Model {candidate} not found/supported. Switching to fallback model.")
                    break

    raise RuntimeError(
        f"Groq API failed after attempting candidate models {candidate_models}: {type(last_error).__name__} - {last_error}"
    )