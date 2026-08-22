"""
Bot sozlamalari
"""
import os
from pathlib import Path


def _load_env():
    env_file = Path(__file__).with_name(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "demo")

CHECK_SECRET = os.getenv("CHECK_SECRET", "")

AVAILABLE_SYMBOLS = [s.strip() for s in os.getenv("AVAILABLE_SYMBOLS", "EUR/USD,USD/JPY,BTC/USD").split(",") if s.strip()]

SYMBOLS = ["EUR/USD"]
INTERVAL = "15min"

CHECK_INTERVAL_SECONDS = 60
