import os

from dotenv import load_dotenv


# .env file ki values load karo
load_dotenv()


# =========================
# GROQ CONFIGURATION
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")


# =========================
# LLM SETTINGS
# =========================

TEMPERATURE = 0.4
MAX_TOKENS = 1200


# =========================
# CHAT HISTORY SETTINGS
# =========================

MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_CHARS = 6000


# =========================
# RAG SETTINGS
# =========================

RAG_MIN_SCORE = 0.35
MAX_RAG_CHUNKS = 4


# =========================
# PROMPT VERSION
# =========================

PROMPT_VERSION = "v1.0"