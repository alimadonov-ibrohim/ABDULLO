import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Vercel serverless: faqat /tmp yoziladigan, DB va loglar u yerda saqlanadi
IS_SERVERLESS = bool(os.getenv("VERCEL"))

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# Masalan: "socks5://user:pass@host:1080" yoki "http://host:8080" (bo'sh = to'g'ri ulanish)
PROXY_URL: str = os.getenv("PROXY_URL", "").strip()

ADMIN_IDS: list[int] = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "123456789").replace(" ", "").split(",")
    if x.strip().isdigit()
]

CHANNEL_ID: str = os.getenv("CHANNEL_ID", "")

_DB_NAME: str = os.getenv("DB_NAME", "trading_bot.db")
if IS_SERVERLESS:
    _tmp = Path(os.getenv("TMPDIR", "/tmp"))
    DB_PATH: str = str(_tmp / _DB_NAME)
    LOGS_DIR: Path = _tmp / "logs"
else:
    DB_PATH = str(BASE_DIR / _DB_NAME)
    LOGS_DIR: Path = BASE_DIR / "logs"

BOT_LOG_FILE: str = str(LOGS_DIR / "bot.log")
ERROR_LOG_FILE: str = str(LOGS_DIR / "bot_err.log")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# --- Vercel webhook rejimi ---
WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "").strip()
CHECK_SECRET: str = os.getenv("CHECK_SECRET", "").strip()

CRYPTO_PAIRS: list[dict] = [
    {"symbol": "BTCUSDT", "screener": "crypto", "exchange": "BINANCE", "title": "BTC/USDT"},
    {"symbol": "ETHUSDT", "screener": "crypto", "exchange": "BINANCE", "title": "ETH/USDT"},
    {"symbol": "SOLUSDT", "screener": "crypto", "exchange": "BINANCE", "title": "SOL/USDT"},
    {"symbol": "XRPUSDT", "screener": "crypto", "exchange": "BINANCE", "title": "XRP/USDT"},
    {"symbol": "BNBUSDT", "screener": "crypto", "exchange": "BINANCE", "title": "BNB/USDT"},
]

FOREX_PAIRS: list[dict] = [
    {"symbol": "EURUSD", "screener": "forex", "exchange": "FX_IDC", "title": "EUR/USD"},
    {"symbol": "GBPUSD", "screener": "forex", "exchange": "FX_IDC", "title": "GBP/USD"},
    {"symbol": "USDJPY", "screener": "forex", "exchange": "FX_IDC", "title": "USD/JPY"},
    {"symbol": "AUDUSD", "screener": "forex", "exchange": "FX_IDC", "title": "AUD/USD"},
    # XAUUSD TradingView'da 'cfd' screeneriga ko'chirilgan
    {"symbol": "XAUUSD", "screener": "cfd", "exchange": "OANDA", "title": "GOLD (XAU/USD)"},
]

ALL_PAIRS: list[dict] = CRYPTO_PAIRS + FOREX_PAIRS

ALL_SYMBOLS: list[str] = [p["symbol"] for p in ALL_PAIRS]

PAIRS_BY_SYMBOL: dict[str, dict] = {p["symbol"].upper(): p for p in ALL_PAIRS}

TIMEFRAMES: list[str] = ["15m", "1h", "4h", "1d"]
TF_LABELS: dict[str, str] = {"15m": "M15", "1h": "H1", "4h": "H4", "1d": "D1"}

TF_WEIGHTS: dict[str, float] = {
    "15m": 0.10,
    "1h": 0.20,
    "4h": 0.35,
    "1d": 0.35,
}

SCAN_INTERVAL_MINUTES: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "60"))
AUTO_SIGNAL_MIN_CONFIDENCE: int = int(os.getenv("AUTO_SIGNAL_MIN_CONFIDENCE", "75"))
SIGNAL_COOLDOWN_HOURS: int = int(os.getenv("SIGNAL_COOLDOWN_HOURS", "8"))

MAX_RISK_PERCENT: float = float(os.getenv("MAX_RISK_PERCENT", "1.5"))

RR_MULTIPLES: list[float] = [1.0, 2.0, 3.0]
SL_ATR_MULTIPLIER: float = 1.5

VIP_PLANS: dict[str, dict] = {
    "month": {
        "label": "1 oylik VIP",
        "days": 30,
        "price_usd": 25,
        "description": "kuniga 3-5 signal",
    },
    "quarter": {
        "label": "3 oylik VIP",
        "days": 90,
        "price_usd": 60,
        "description": "20% tejamkor",
    },
    "year": {
        "label": "1 yillik VIP",
        "days": 365,
        "price_usd": 180,
        "description": "eng ommabop, 40% tejamkor",
    },
}

TWELVE_DATA_API_KEY: str = os.getenv("TWELVEDATA_API_KEY", "")
BINANCE_API_BASE: str = os.getenv("BINANCE_API_BASE", "https://api.binance.com")

REQUEST_TIMEOUT: int = 20
TV_CONCURRENCY_LIMIT: int = 6


def get_pair_meta(symbol: str) -> dict | None:
    return PAIRS_BY_SYMBOL.get(symbol.strip().upper())


def guess_pair_meta(symbol: str) -> dict:
    s = symbol.strip().upper()
    meta = get_pair_meta(s)
    if meta:
        return meta
    if s.endswith(("USDT", "USDC", "BUSD", "FDUSD")):
        return {"symbol": s, "screener": "crypto", "exchange": "BINANCE", "title": f"{s[:-4]}/{s[-4:]}"}
    return {"symbol": s, "screener": "forex", "exchange": "FX_IDC", "title": s}
