from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    import talib

    HAS_TALIB = True
except ImportError:
    talib = None
    HAS_TALIB = False

BULL = "BULLISH"
BEAR = "BEARISH"
NEUTRAL = "NEUTRAL"


@dataclass
class PatternHit:
    name: str
    direction: str
    strength: int


@dataclass
class ChartFigure:
    name: str
    direction: str
    neckline: float | None = None


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _range(h: float, l: float) -> float:
    return max(h - l, 1e-12)


def _fallback_doji(df: pd.DataFrame) -> list[PatternHit]:
    hits = []
    for i in range(1, len(df)):
        o, h, l, c = df["open"].iat[i], df["high"].iat[i], df["low"].iat[i], df["close"].iat[i]
        body = _body(o, c)
        rng = _range(h, l)
        if body <= 0.08 * rng and rng > 0:
            hits.append(PatternHit("Doji", NEUTRAL, 2))
            break
    return hits


def _fallback_engulfing(df: pd.DataFrame) -> list[PatternHit]:
    hits = []
    n = len(df)
    if n < 2:
        return hits
    po, pc = df["open"].iat[-2], df["close"].iat[-2]
    co, cc = df["open"].iat[-1], df["close"].iat[-1]
    prev_body = _body(po, pc)
    cur_body = _body(co, cc)
    if prev_body > 0 and cur_body >= prev_body:
        if pc < po and cc > co and cc >= po and co >= pc:
            hits.append(PatternHit("Bullish Engulfing", BULL, 4))
        elif pc > po and cc < co and cc <= po and co <= pc:
            hits.append(PatternHit("Bearish Engulfing", BEAR, 4))
    return hits


def _fallback_hammer_shooting_star(df: pd.DataFrame) -> list[PatternHit]:
    hits = []
    o, h, l, c = (
        df["open"].iat[-1],
        df["high"].iat[-1],
        df["low"].iat[-1],
        df["close"].iat[-1],
    )
    body = _body(o, c)
    upper = h - max(o, c)
    lower = min(o, c) - l
    rng = _range(h, l)
    if body <= 0.45 * rng and body > 0:
        if lower >= 2 * body and upper <= 0.5 * body:
            hits.append(PatternHit("Hammer", BULL, 3))
        elif upper >= 2 * body and lower <= 0.5 * body:
            hits.append(PatternHit("Shooting Star", BEAR, 3))
    return hits


def _talib_patterns(df: pd.DataFrame, lookback: int = 3) -> list[PatternHit]:
    o = df["open"].to_numpy(dtype=np.float64)
    h = df["high"].to_numpy(dtype=np.float64)
    l = df["low"].to_numpy(dtype=np.float64)
    c = df["close"].to_numpy(dtype=np.float64)

    catalog = {
        "Doji": (talib.CDLDOJI, NEUTRAL),
        "Hammer": (talib.CDLHAMMER, BULL),
        "Inverted Hammer": (talib.CDLINVERTEDHAMMER, BULL),
        "Bullish Engulfing": (None, BULL),
        "Morning Star": (talib.CDLMORNINGSTAR, BULL),
        "Piercing Line": (talib.CDLPIERCING, BULL),
        "Three White Soldiers": (talib.CDL3WHITESOLDIERS, BULL),
        "Shooting Star": (talib.CDLSHOOTINGSTAR, BEAR),
        "Evening Star": (talib.CDLEVENINGSTAR, BEAR),
        "Dark Cloud Cover": (talib.CDLDARKCLOUDCOVER, BEAR),
        "Three Black Crows": (talib.CDL3BLACKCROWS, BEAR),
        "Hanging Man": (talib.CDLHANGINGMAN, BEAR),
    }

    hits: dict[str, PatternHit] = {}
    tail_start = max(0, len(df) - lookback)

    def register(code_arr, name, direction):
        codes = code_arr[tail_start:]
        strength = int(np.max(np.abs(codes))) if len(codes) else 0
        if strength >= 100:
            hits[name] = PatternHit(name, direction, min(strength // 20, 5))

    for name, (fn, direction) in catalog.items():
        if fn is not None:
            try:
                register(fn(o, h, l, c), name, direction)
            except Exception:
                continue

    eng_bull = talib.CDLENGULFING(o, h, l, c)[tail_start:]
    if np.any(eng_bull > 0):
        hits["Bullish Engulfing"] = PatternHit("Bullish Engulfing", BULL, 4)
    if np.any(eng_bull < 0):
        hits["Bearish Engulfing"] = PatternHit("Bearish Engulfing", BEAR, 4)

    return list(hits.values())


def scan_candle_patterns(df: pd.DataFrame | None) -> list[PatternHit]:
    if df is None or len(df) < 10:
        return []
    if HAS_TALIB:
        try:
            return _talib_patterns(df)
        except Exception:
            pass
    found = []
    found.extend(_fallback_doji(df.tail(6)))
    found.extend(_fallback_engulfing(df))
    found.extend(_fallback_hammer_shooting_star(df))
    return found


def _local_extrema(values: np.ndarray, order: int = 3):
    peaks, troughs = [], []
    n = len(values)
    for i in range(order, n - order):
        window = values[i - order : i + order + 1]
        if values[i] == window.max() and (window.argmax() == order or values[i] > window[:order].max()):
            peaks.append(i)
        if values[i] == window.min() and (window.argmin() == order or values[i] < window[:order].min()):
            troughs.append(i)
    return peaks, troughs


def detect_head_and_shoulders(
    df: pd.DataFrame | None,
    lookback: int = 90,
    order: int = 4,
    tolerance: float = 0.025,
) -> ChartFigure | None:
    if df is None or len(df) < lookback:
        return None
    closes = df["close"].to_numpy(dtype=np.float64)[-lookback:]
    peaks, troughs = _local_extrema(closes, order=order)

    for i in range(len(peaks) - 2):
        p1, p2, p3 = closes[peaks[i]], closes[peaks[i + 1]], closes[peaks[i + 2]]
        if p2 <= p1 or p2 <= p3:
            continue
        shoulder_diff = abs(p1 - p3) / p2
        if shoulder_diff <= tolerance and p1 < p2 and p3 < p2:
            t_between = [t for t in troughs if peaks[i] < t < peaks[i + 2]]
            if len(t_between) >= 2:
                neckline = (closes[t_between[0]] + closes[t_between[-1]]) / 2
                return ChartFigure("Head & Shoulders", BEAR, round(float(neckline), 8))

    for i in range(len(troughs) - 2):
        t1, t2, t3 = closes[troughs[i]], closes[troughs[i + 1]], closes[troughs[i + 2]]
        if t2 >= t1 or t2 >= t3:
            continue
        shoulder_diff = abs(t1 - t3) / t2 if t2 != 0 else 1
        if shoulder_diff <= tolerance and t1 > t2 and t3 > t2:
            p_between = [p for p in peaks if troughs[i] < p < troughs[i + 2]]
            if len(p_between) >= 2:
                neckline = (closes[p_between[0]] + closes[p_between[-1]]) / 2
                return ChartFigure(
                    "Inverse Head & Shoulders", BULL, round(float(neckline), 8)
                )
    return None


def detect_double_top_bottom(
    df: pd.DataFrame | None,
    lookback: int = 90,
    order: int = 4,
    tolerance: float = 0.01,
) -> ChartFigure | None:
    if df is None or len(df) < lookback:
        return None
    highs = df["high"].to_numpy(dtype=np.float64)[-lookback:]
    lows = df["low"].to_numpy(dtype=np.float64)[-lookback:]
    high_peaks, _ = _local_extrema(highs, order=order)
    _, low_troughs = _local_extrema(lows, order=order)

    if len(high_peaks) >= 2:
        a, b = high_peaks[-2], high_peaks[-1]
        if abs(highs[a] - highs[b]) / highs[b] <= tolerance:
            return ChartFigure("Double Top", BEAR)
    if len(low_troughs) >= 2:
        a, b = low_troughs[-2], low_troughs[-1]
        if abs(lows[a] - lows[b]) / lows[b] <= tolerance:
            return ChartFigure("Double Bottom", BULL)
    return None


def scan_chart_figures(df: pd.DataFrame | None) -> list[ChartFigure]:
    figures = []
    hs = detect_head_and_shoulders(df)
    if hs:
        figures.append(hs)
    dtb = detect_double_top_bottom(df)
    if dtb:
        figures.append(dtb)
    return figures


def summarize_patterns(
    patterns: list[PatternHit],
    figures: list[ChartFigure],
    lang: str = "uz",
) -> str:
    from utils.i18n import pattern_name, t

    parts = []
    for p in patterns[:4]:
        icon = {"BULLISH": "🟢", "BEARISH": "🔴"}.get(p.direction, "⚪")
        parts.append(f"{icon} {pattern_name(p.name, lang)}")
    for fig in figures[:2]:
        icon = {"BULLISH": "🟢", "BEARISH": "🔴"}.get(fig.direction, "⚪")
        suffix = (
            f" ({t(lang, 'neckline_lbl')}: {fig.neckline})" if fig.neckline else ""
        )
        parts.append(f"{icon} {pattern_name(fig.name, lang)}{suffix}")
    return ", ".join(parts) if parts else t(lang, "patterns_none")


def pattern_bias_bonus(patterns: list[PatternHit], figures: list[ChartFigure], direction: str) -> int:
    want = BULL if direction == "LONG" else BEAR if direction == "SHORT" else None
    if want is None:
        return 0
    score = 0
    for hit in patterns:
        if hit.direction == want:
            score += 2
    for fig in figures:
        if fig.direction == want:
            score += 3
    return min(score, 8)
