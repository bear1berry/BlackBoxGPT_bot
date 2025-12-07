from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise ValueError(f"CRITICAL: Env var '{name}' is missing!")
    return val or ""

# Bot
BOT_TOKEN = _get_env("BOT_TOKEN", required=True)
BOT_USERNAME = _get_env("BOT_USERNAME", "BlackBoxAI_Bot")
ADMIN_IDS = [int(x) for x in _get_env("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# LLM
DEEPSEEK_API_KEY = _get_env("DEEPSEEK_API_KEY", required=True)
DEEPSEEK_BASE_URL = _get_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_URL = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
DEEPSEEK_MODEL = _get_env("DEEPSEEK_MODEL", "deepseek-chat")

# Audio (Yandex)
AUDIO_PROVIDER = _get_env("AUDIO_PROVIDER", "yandex")
YANDEX_SPEECHKIT_API_KEY = _get_env("YANDEX_SPEECHKIT_API_KEY", "")
YANDEX_FOLDER_ID = _get_env("YANDEX_FOLDER_ID", "")

# Crypto
CRYPTO_PAY_API_URL = "https://pay.crypt.bot/api/"
CRYPTO_PAY_API_TOKEN = _get_env("CRYPTO_PAY_API_TOKEN", "")

# Limits
PLAN_FREE_DAILY_LIMIT = int(_get_env("FREE_DAILY_LIMIT", "20"))
PLAN_PREMIUM_DAILY_LIMIT = int(_get_env("PREMIUM_DAILY_LIMIT", "200"))

# Tariffs
SUBSCRIPTION_TARIFFS = {
    "month_1": {"code": "premium_1m", "title": "Premium · 1 мес", "months": 1, "price_usdt": "7.99"},
    "month_3": {"code": "premium_3m", "title": "Premium · 3 мес", "months": 3, "price_usdt": "26.99"},
    "month_12": {"code": "premium_12m", "title": "Premium · 12 мес", "months": 12, "price_usdt": "82.99"},
}
