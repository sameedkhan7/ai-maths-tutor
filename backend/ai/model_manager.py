import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("model_manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "model_config.json")

DEFAULT_MODEL_CONFIG = {
    "force_local_only": False,
    "local_rtx_enabled": True,
    "groq_enabled": True,
    "allowed_models": {
        "qwen2.5:7b": True,
        "openai/gpt-oss-120b": True,
        "openai/gpt-oss-20b": True,
        "qwen/qwen3.8-27b": True,
        "allam-2-7b": True
    },
    "default_model": "openai/gpt-oss-120b",
    "last_updated": None
}

def get_model_config() -> dict:
    """Reads current model ON/OFF configuration from data/model_config.json."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = dict(DEFAULT_MODEL_CONFIG)
                cfg.update(data)
                if "allowed_models" in data and isinstance(data["allowed_models"], dict):
                    allowed = dict(DEFAULT_MODEL_CONFIG["allowed_models"])
                    allowed.update(data["allowed_models"])
                    cfg["allowed_models"] = allowed
                return cfg
    except Exception as e:
        logger.warning(f"Could not read {CONFIG_PATH} ({e}), using default model config")
    return dict(DEFAULT_MODEL_CONFIG)

def update_model_config(new_config: dict) -> dict:
    """Safely updates model ON/OFF configuration to data/model_config.json."""
    try:
        current = get_model_config()
        if "force_local_only" in new_config:
            current["force_local_only"] = bool(new_config["force_local_only"])
        if "local_rtx_enabled" in new_config:
            current["local_rtx_enabled"] = bool(new_config["local_rtx_enabled"])
        if "groq_enabled" in new_config:
            current["groq_enabled"] = bool(new_config["groq_enabled"])
        if "allowed_models" in new_config and isinstance(new_config["allowed_models"], dict):
            current["allowed_models"].update({str(k): bool(v) for k, v in new_config["allowed_models"].items()})
        if "default_model" in new_config and new_config["default_model"]:
            current["default_model"] = str(new_config["default_model"])

        current["last_updated"] = datetime.now().isoformat()

        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return current
    except Exception as e:
        logger.error(f"Failed to save model configuration: {e}")
        raise e
