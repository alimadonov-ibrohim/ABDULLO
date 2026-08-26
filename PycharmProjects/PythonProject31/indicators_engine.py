import asyncio
import math
import time
from dataclasses import dataclass, field

import aiohttp
import pandas as pd
from tradingview_ta import TA_Handler

import config


@dataclass
class TimeframeSnapshot:
    timeframe: str
    close: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None
    adx: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    ichimoku_base: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    tv_recommendation: str = ""
    tv_score: float = 0.0
    summary_buy: int = 0
    summary_sell: int = 0
    summary_neutral: int = 0
    score: int = 0
    verdict: str = "NEUTRAL"


@dataclass
class AnalysisResult:
    symbol: str
    title: str
    screener: str
    exchange: str
    snapshots: dict[str, TimeframeSnapshot] = field(default_factory=dict)
    combined_score: float = 0.0
    direction: str = "NEUTRAL"
    confidence: int = 50
    supports: list[float] = field(default_factory=list)
    resistances: list[float] = field(default_factory=list)
    atr: float | None = None
    last_price: float | None = None
    ohlc: pd.DataFrame | None = None
    tv_ok: int = 0  # ma'lumot olgan timeframe'lar soni


def _pick(indicators: dict, *keys):
    for key in keys:
        val = indicators.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    return None


def _parse_snapshot(timeframe: str, analysis) -> TimeframeSnapshot:
    snap = TimeframeSnapshot(timeframe=timeframe)
    try:
        ind = dict(getattr(analysis, "indicators", {}) or {})
    except Exception:
        ind = {}

    snap.close = _pick(ind, "close", "Price Abs")
    snap.rsi = _pick(ind, "RSI")
    snap.macd = _pick(ind, "MACD.macd")
    snap.macd_signal = _pick(ind, "MACD.signal")
    snap.stoch_k = _pick(ind, "Stoch.K")
    snap.stoch_d = _pick(ind, "Stoch.D")
    snap.adx = _pick(ind, "ADX")
    snap.plus_di = _pick(ind, "ADX+DI", "PDI", "+DI")
    snap.minus_di = _pick(ind, "ADX-DI", "MDI", "-DI")
    snap.ema50 = _pick(ind, "EMA50")
    snap.ema200 = _pick(ind, "EMA200")
    snap.ichimoku_base = _pick(
        ind, "Ichimoku.BLine", "Ichimoku.Base.Line", "Ichimoku_Base_Line"
    )

    try:
        summary = getattr(analysis, "summary", {}) or {}
        snap.tv_recommendation = summary.get("RECOMMENDATION", "")
        snap.summary_buy = int(summary.get("BUY") or 0)
        snap.summary_sell = int(summary.get("SELL") or 0)
        snap.summary_neutral = int(summary.get("NEUTRAL") or 0)
    except Exception:
        pass

    rec_all = _pick(ind, "Recommend.All") or 0.0
    snap.tv_score = max(-1.0, min(1.0, rec_all))
    return snap


def _fetch_tv_sync(symbol: str, screener: str, exchange: str, interval: str):
    handler = TA_Handler(symbol=symbol, screener=screener, exchange=exchange, interval=interval)
    return handler.get_analysis()


# TradingView ba'zan simvollarni screenerlar orasida ko'chirib yuritadi
# (masalan XAUUSD forex -> cfd). Ishlamasa — fallback screeners sinanadi.
FALLBACK_SCREENERS: dict[str, list[str]] = {
    "forex": ["cfd"],
    "cfd": ["forex"],
}

# TV javoblari keshi: {key: (expires_at, snapshot)} — rate-limit'ga qarshi
_TV_CACHE: dict[tuple, tuple[float, TimeframeSnapshot]] = {}
_TV_CACHE_TTL = 480  # 8 daqiqa — ratinglar tez o'zgarmaydi
_TV_RETRY_DELAYS = (2.0, 5.0, 10.0)


async def fetch_timeframe(
    symbol: str,
    screener: str,
    exchange: str,
    interval: str,
    semaphore: asyncio.Semaphore,
) -> TimeframeSnapshot:
    cache_key = (symbol, screener, exchange, interval)
    now = time.monotonic()
    cached = _TV_CACHE.get(cache_key)
    if cached and cached[0] > now:
        return cached[1]

    async with semaphore:
        screeners = [screener] + [
            s for s in FALLBACK_SCREENERS.get(screener, []) if s != screener
        ]
        # Har bir screener uchun 429 bo'lsa ortga surib qayta urinish
        for scr in screeners:
            for delay in _TV_RETRY_DELAYS:
                try:
                    analysis = await asyncio.to_thread(
                        _fetch_tv_sync, symbol, scr, exchange, interval
                    )
                    snap = _parse_snapshot(interval, analysis)
                    if snap.close is not None:
                        _TV_CACHE[cache_key] = (
                            time.monotonic() + _TV_CACHE_TTL,
                            snap,
                        )
                        return snap
                    break  # javob bor lekin bo'sh — boshqa screenerga o'tish
                except Exception as exc:
                    if "429" not in str(exc):
                        break  # boshqa xato — boshqa screenerga o'tish
                    await asyncio.sleep(delay)
        return TimeframeSnapshot(timeframe=interval)


def score_snapshot(snap: TimeframeSnapshot) -> tuple[int, str]:
    if snap.close is None:
        snap.score = 0
        snap.verdict = "NO DATA"
        return 0, snap.verdict

    score = 0.0

    if snap.rsi is not None:
        if snap.rsi <= 30:
            score += 22
        elif snap.rsi >= 70:
            score -= 22
        else:
            score += (snap.rsi - 50) * 0.55

    if snap.macd is not None and snap.macd_signal is not None:
        diff = snap.macd - snap.macd_signal
        ref = max(abs(snap.close) * 0.0005, 1e-9)
        score += max(-16.0, min(16.0, diff / ref * 6))

    if snap.stoch_k is not None and snap.stoch_d is not None:
        score += 11 if snap.stoch_k > snap.stoch_d else -11
        if snap.stoch_k <= 20:
            score += 7
        elif snap.stoch_k >= 80:
            score -= 7

    if snap.ema50 is not None:
        score += 12 if snap.close > snap.ema50 else -12
    if snap.ema50 is not None and snap.ema200 is not None:
        score += 15 if snap.ema50 > snap.ema200 else -15

    if snap.ichimoku_base is not None:
        score += 9 if snap.close > snap.ichimoku_base else -9

    if snap.adx is not None and snap.adx >= 20:
        di_bias = 0.0
        if snap.plus_di is not None and snap.minus_di is not None:
            di_bias = 1 if snap.plus_di > snap.minus_di else -1
        elif snap.tv_score != 0:
            di_bias = 1 if snap.tv_score > 0 else -1
        strength = min(snap.adx / 50.0, 1.0) * 14
        score += di_bias * strength

    score += snap.tv_score * 18

    snap.score = int(max(-100, min(100, round(score))))
    if snap.score >= 45:
        snap.verdict = "STRONG BUY"
    elif snap.score >= 12:
        snap.verdict = "BUY"
    elif snap.score <= -45:
        snap.verdict = "STRONG SELL"
    elif snap.score <= -12:
        snap.verdict = "SELL"
    else:
        snap.verdict = "NEUTRAL"
    return snap.score, snap.verdict


async def fetch_binance_ohlc(symbol: str, interval: str, limit: int = 150):
    url = f"{config.BINANCE_API_BASE}/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                raw = await resp.json()
    except Exception:
        return None

    rows = []
    for item in raw:
        try:
            rows.append(
                {
                    "ts": pd.to_datetime(int(item[0]), unit="ms", utc=True),
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5]),
                }
            )
        except (ValueError, IndexError, TypeError):
            continue
    if len(rows) < 60:
        return None
    return pd.DataFrame(rows)


TD_INTERVALS = {"15m": "15min", "1h": "1h", "4h": "4h", "1d": "1day"}


async def fetch_twelvedata_ohlc(symbol: str, interval: str, limit: int = 150):
    if not config.TWELVE_DATA_API_KEY:
        return None
    pair = symbol.upper()
    if pair.startswith(("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD")):
        pair = f"{pair[:-3]}/{pair[-3:]}"
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": pair,
        "interval": TD_INTERVALS.get(interval, interval),
        "outputsize": limit,
        "apikey": config.TWELVE_DATA_API_KEY,
        "order": "ASC",
    }
    timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                payload = await resp.json()
    except Exception:
        return None

    values = payload.get("values") if isinstance(payload, dict) else None
    if not values or len(values) < 60:
        return None
    rows = []
    for item in values:
        try:
            rows.append(
                {
                    "ts": pd.to_datetime(item.get("datetime"), utc=True),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item.get("volume") or 0),
                }
            )
        except (ValueError, KeyError, TypeError):
            continue
    if len(rows) < 60:
        return None
    return pd.DataFrame(rows)


def compute_atr(df: pd.DataFrame, period: int = 14) -> float | None:
    if df is None or len(df) < period + 2:
        return None
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return round(float(tr.rolling(period).mean().iloc[-1]), 8)


def compute_bollinger(df: pd.DataFrame, period: int = 20, ndev: float = 2.0):
    if df is None or len(df) < period:
        return None, None
    mid = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std(ddof=0)
    return (
        round(float(mid.iloc[-1] + ndev * std.iloc[-1]), 8),
        round(float(mid.iloc[-1] - ndev * std.iloc[-1]), 8),
    )


def compute_support_resistance(df: pd.DataFrame, tolerance: float = 0.004):
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    window = 5
    n = len(highs)

    swing_highs, swing_lows = [], []
    for i in range(window, n - window):
        seg_h = highs[i - window : i + window + 1]
        seg_l = lows[i - window : i + window + 1]
        if highs[i] >= max(seg_h):
            swing_highs.append(highs[i])
        if lows[i] <= min(seg_l):
            swing_lows.append(lows[i])

    def cluster(levels: list[float]) -> list[float]:
        if not levels:
            return []
        levels_sorted = sorted(levels)
        groups: list[list[float]] = [[levels_sorted[0]]]
        for lv in levels_sorted[1:]:
            base = sum(groups[-1]) / len(groups[-1])
            if abs(lv - base) / base <= tolerance:
                groups[-1].append(lv)
            else:
                groups.append([lv])
        merged = [round(sum(g) / len(g), 8) for g in groups]
        counts = {m: len(g) for m, g in zip(merged, groups)}
        merged.sort(key=lambda x: counts[x], reverse=True)
        return merged

    return cluster(swing_lows), cluster(swing_highs)


# Qisqa muddatli kesh: bir juftlikni qayta-qayta so'rash TradingView'ni
# yana so'ramaydi (serverless warm instansiyada tez javob uchun).
_ANALYSIS_CACHE: dict[str, tuple[float, "AnalysisResult"]] = {}
_ANALYSIS_TTL_SEC = 60
_ANALYSIS_CACHE_MAX = 32


async def analyze_symbol(symbol: str, meta: dict | None = None, with_ohlc: bool = True) -> AnalysisResult:
    meta = meta or config.guess_pair_meta(symbol)
    cache_key = f"{meta['symbol']}:{'ohlc' if with_ohlc else 'no'}"
    now = time.monotonic()
    hit = _ANALYSIS_CACHE.get(cache_key)
    if hit is not None and now - hit[0] < _ANALYSIS_TTL_SEC:
        return hit[1]

    symbol_u = meta["symbol"]
    result = AnalysisResult(
        symbol=symbol_u,
        title=meta.get("title", symbol_u),
        screener=meta.get("screener", "crypto"),
        exchange=meta.get("exchange", "BINANCE"),
    )

    semaphore = asyncio.Semaphore(config.TV_CONCURRENCY_LIMIT)
    tasks = [
        fetch_timeframe(symbol_u, result.screener, result.exchange, tf, semaphore)
        for tf in config.TIMEFRAMES
    ]
    ohlc_task = None
    if with_ohlc:
        if result.screener == "crypto":
            ohlc_task = fetch_binance_ohlc(symbol_u, "4h")
        else:
            ohlc_task = fetch_twelvedata_ohlc(symbol_u, "4h")

    gathered = await asyncio.gather(*tasks, ohlc_task) if ohlc_task else await asyncio.gather(*tasks)
    snaps = gathered[: len(tasks)]
    ohlc = gathered[len(tasks)] if ohlc_task else None

    for snap in snaps:
        score_snapshot(snap)
        result.snapshots[snap.timeframe] = snap
    result.tv_ok = sum(1 for s in snaps if s.close is not None)

    primary = result.snapshots.get("4h") or result.snapshots.get("1h") or snaps[0]
    result.last_price = primary.close

    total_weight = 0.0
    weighted_sum = 0.0
    for tf, snap in result.snapshots.items():
        w = config.TF_WEIGHTS.get(tf, 0.25)
        weighted_sum += snap.score * w
        total_weight += w
    result.combined_score = round(weighted_sum / total_weight, 1) if total_weight else 0.0

    if result.combined_score >= 25:
        result.direction = "LONG"
    elif result.combined_score <= -25:
        result.direction = "SHORT"

    if ohlc is not None:
        result.ohlc = ohlc
        result.atr = compute_atr(ohlc)
        bb_up, bb_low = compute_bollinger(ohlc)
        if bb_up and bb_low:
            primary.bb_upper = bb_up
            primary.bb_lower = bb_low
        supports, resistances = compute_support_resistance(ohlc)
        price = result.last_price or ohlc["close"].iloc[-1]
        result.supports = sorted([s for s in supports if s < price], reverse=True)[:3]
        result.resistances = sorted([r for r in resistances if r > price])[:3]

    if not result.supports and primary.ema200:
        result.supports = [primary.ema200]
    if not result.resistances and primary.ema200:
        result.resistances = [primary.ema200]

    agree = sum(
        1
        for s in snaps
        if (result.direction == "LONG" and s.score >= 12)
        or (result.direction == "SHORT" and s.score <= -12)
    )
    base_conf = 38 + min(abs(result.combined_score), 90) * 0.42
    adx_bonus = min((primary.adx or 0) / 2.5, 8.0)
    result.confidence = int(max(35, min(93, base_conf + agree * 4 + adx_bonus)))

    if len(_ANALYSIS_CACHE) >= _ANALYSIS_CACHE_MAX:
        oldest_key = min(_ANALYSIS_CACHE, key=lambda k: _ANALYSIS_CACHE[k][0])
        _ANALYSIS_CACHE.pop(oldest_key, None)
    _ANALYSIS_CACHE[cache_key] = (time.monotonic(), result)
    return result


def format_levels(levels: list[float], decimals: int | None = None) -> str:
    if not levels:
        return "-"
    dec = decimals if decimals is not None else auto_decimals(levels[0])
    return ", ".join(f"{lv:.{dec}f}" for lv in levels)


def auto_decimals(price: float | None) -> int:
    if price is None or math.isnan(price):
        return 2
    if price >= 1000:
        return 2
    if price >= 10:
        return 3
    if price >= 0.5:
        return 4
    if price >= 0.01:
        return 5
    return 7


def fmt_price(price: float | None, decimals: int | None = None) -> str:
    if price is None:
        return "-"
    dec = decimals if decimals is not None else auto_decimals(price)
    return f"{price:.{dec}f}"
