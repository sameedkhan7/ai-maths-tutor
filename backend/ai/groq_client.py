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


def call_ollama(messages: list[dict], model: str = "qwen2.5:7b") -> str | None:
    """
    Sends prompt to local Ollama or local LLM server running on RTX GPU.
    Supports both native Ollama (/api/chat) and OpenAI-compatible endpoints (/v1/chat/completions),
    with optional API key authentication (OLLAMA_API_KEY or LOCAL_LLM_KEY).
    """
    import os
    import requests
    import logging

    logger = logging.getLogger("groq_client")
    raw_url = os.getenv("OLLAMA_URL") or os.getenv("LOCAL_LLM_URL") or "http://localhost:11434"
    raw_url = raw_url.rstrip("/")

    # Detect endpoint format
    if raw_url.endswith("/v1/chat/completions") or raw_url.endswith("/api/chat"):
        ollama_url = raw_url
    elif raw_url.endswith("/v1"):
        ollama_url = f"{raw_url}/chat/completions"
    else:
        ollama_url = f"{raw_url}/api/chat"

    api_key = (os.getenv("OLLAMA_API_KEY") or os.getenv("LOCAL_LLM_KEY") or "").strip()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    is_v1 = "chat/completions" in ollama_url
    if is_v1:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS
        }
    else:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        }

    try:
        logger.info(f"[Local Qwen] Calling RTX GPU at {ollama_url} (model={model})")
        resp = requests.post(ollama_url, json=payload, headers=headers, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            if is_v1:
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                content = data.get("message", {}).get("content", "")
            if content and content.strip():
                logger.info(f"[Local Qwen] Received response from RTX GPU ({len(content)} chars)")
                return content
    except Exception as e:
        logger.info(f"[Local Qwen] Local RTX connection not reached ({e}). Falling back to cloud...")
    return None


def call_qwen_cloud(messages: list[dict], model: str = "qwen-plus") -> str | None:
    """Sends prompt to Alibaba Cloud Qwen DashScope API using QWEN_API_KEY."""
    import os
    import requests
    import logging

    api_key = os.getenv("QWEN_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions").strip()
    if not base_url.endswith("/chat/completions"):
        base_url = base_url.rstrip("/") + "/chat/completions"
    try:
        resp = requests.post(
            base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS
            },
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.getLogger("groq_client").warning(f"[Qwen Cloud] API call failed: {e}")
    return None


def call_groq(
    messages: list[dict],
    model: str | None = None,
    retries: int = 3,
) -> str:
    """
    Send messages to local Ollama (if selected or available) or Groq with cascade fallback and retry logic.
    """
    import logging
    import time
    import os

    logger = logging.getLogger("groq_client")

    # 1. Check if Local RTX Qwen / Ollama model is requested
    use_local_env = os.getenv("USE_LOCAL_LLM", "").lower() in ("true", "1", "yes")
    is_local_model_requested = bool(model and ("qwen2.5" in model.lower() or "local" in model.lower()))

    if is_local_model_requested or use_local_env:
        local_target = model if (model and "qwen2.5" in model.lower()) else "qwen2.5:7b"
        local_result = call_ollama(messages, model=local_target)
        if local_result:
            return local_result
        logger.info(f"[LLM Router] Local model '{local_target}' not reached. Falling back to Cloud...")

    # 2. Check if official Qwen Cloud API key is configured
    qwen_api_key = os.getenv("QWEN_API_KEY", "").strip()
    if qwen_api_key and (is_local_model_requested or "qwen" in (model or "").lower()):
        cloud_target = os.getenv("QWEN_MODEL", "qwen-plus")
        cloud_result = call_qwen_cloud(messages, model=cloud_target)
        if cloud_result:
            return cloud_result

    client = create_groq_client()
    default_model = GROQ_MODEL or "openai/gpt-oss-120b"
    primary_model = model or default_model

    # If local model was requested but failed, fallback to cloud default
    if "qwen2.5" in primary_model.lower() or "local" in primary_model.lower():
        primary_model = default_model

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