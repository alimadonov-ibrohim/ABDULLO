from __future__ import annotations

from dataclasses import dataclass

import config
from indicators_engine import (
    AnalysisResult,
    TimeframeSnapshot,
    auto_decimals,
    fmt_price,
)
from pattern_scanner import ChartFigure, PatternHit, pattern_bias_bonus


@dataclass
class TradingSignal:
    symbol: str
    title: str
    exchange: str
    screener: str
    direction: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    sl_percent: float
    confidence: int
    rr_ratio: float
    combined_score: float
    adx_4h: float | None
    patterns_text: str
    supports: list[float]
    resistances: list[float]
    decimals: int


def _sl_distance_for(
    result: AnalysisResult, direction: str, entry: float
) -> tuple[float, float]:
    atr = result.atr or 0.0
    atr_based = atr * config.SL_ATR_MULTIPLIER if atr > 0 else entry * 0.008

    level_based = 0.0
    levels = result.supports if direction == "LONG" else result.resistances
    for lv in levels:
        dist = abs(entry - lv)
        if dist > entry * 0.0005:
            level_based = dist
            break

    distance = max(atr_based, level_based * 0.9 if level_based else atr_based)
    distance = max(distance, entry * 0.0025)
    distance = min(distance, entry * 0.05)

    if direction == "LONG":
        return entry - distance, distance
    return entry + distance, distance


def generate_signal(
    result: AnalysisResult,
    patterns: list[PatternHit],
    figures: list[ChartFigure],
) -> TradingSignal | None:
    if result.direction == "NEUTRAL" or result.last_price is None:
        return None

    entry = float(result.last_price)
    sl_price, sl_distance = _sl_distance_for(result, result.direction, entry)
    dec = auto_decimals(entry)

    tps = [
        round(entry + d * mult if result.direction == "LONG" else entry - d * mult, dec + 3)
        for mult in config.RR_MULTIPLES
        for d in [sl_distance]
    ]
    tp1, tp2, tp3 = tps

    conf = result.confidence + pattern_bias_bonus(patterns, figures, result.direction)
    conf = int(max(35, min(95, conf)))

    primary_snap = result.snapshots.get("4h") or next(iter(result.snapshots.values()))
    adx = primary_snap.adx if primary_snap else None

    return TradingSignal(
        symbol=result.symbol,
        title=result.title,
        exchange=result.exchange,
        screener=result.screener,
        direction=result.direction,
        entry=round(entry, dec),
        sl=round(sl_price, dec),
        tp1=round(tp1, dec),
        tp2=round(tp2, dec),
        tp3=round(tp3, dec),
        sl_percent=round(sl_distance / entry * 100, 2),
        confidence=conf,
        rr_ratio=config.RR_MULTIPLES[-1],
        combined_score=result.combined_score,
        adx_4h=adx,
        patterns_text="",
        supports=list(result.supports),
        resistances=list(result.resistances),
        decimals=dec,
    )


def tf_line(snap: TimeframeSnapshot, decimals: int | None = None) -> str:
    icon_map = {
        "STRONG BUY": "🟢🟢",
        "BUY": "🟢",
        "NEUTRAL": "⚪️",
        "SELL": "🔴",
        "STRONG SELL": "🔴🔴",
        "NO DATA": "⚫️",
    }
    icon = icon_map.get(snap.verdict, "⚪️")
    rsi_txt = f"{snap.rsi:.1f}" if snap.rsi is not None else "-"
    adx_txt = f"{snap.adx:.0f}" if snap.adx is not None else "-"
    close_txt = fmt_price(snap.close, decimals)
    return f"<b>{close_txt}</b> | {icon} {snap.verdict:<11} | RSI {rsi_txt} | ADX {adx_txt}"
