import config
import indicators_engine
import pattern_scanner
import signal_generator
from logger import get_logger
from utils.formatters import (
    format_mtf_lines,
    format_neutral_summary,
    format_signal_alert,
    format_signal_message,
)

log = get_logger("services")


async def full_analysis(symbol: str, meta: dict | None = None, lang: str = "uz"):
    result = await indicators_engine.analyze_symbol(symbol, meta=meta)

    patterns = pattern_scanner.scan_candle_patterns(result.ohlc)
    figures = pattern_scanner.scan_chart_figures(result.ohlc)
    patterns_text = pattern_scanner.summarize_patterns(patterns, figures, lang)

    sig = signal_generator.generate_signal(result, patterns, figures)
    mtf_lines = format_mtf_lines(result.snapshots, lang)

    if sig:
        text = format_signal_message(sig, mtf_lines, patterns_text, lang)
    else:
        text = format_neutral_summary(result, mtf_lines, patterns_text, lang)
    return text, result, sig


async def auto_scan_symbol(symbol: str):
    meta = config.get_pair_meta(symbol)
    if not meta:
        return None, None

    result = await indicators_engine.analyze_symbol(symbol, meta=meta)
    if result.direction == "NEUTRAL" or result.last_price is None:
        return None, result

    cooldown = await db_last_signal_recent(result.symbol, result.direction)
    if cooldown:
        log.info("Skip %s %s — cooldown active", result.symbol, result.direction)
        return None, result

    patterns = pattern_scanner.scan_candle_patterns(result.ohlc)
    figures = pattern_scanner.scan_chart_figures(result.ohlc)
    patterns_text = pattern_scanner.summarize_patterns(patterns, figures)

    sig = signal_generator.generate_signal(result, patterns, figures)
    if not sig:
        return None, result

    bonus = pattern_scanner.pattern_bias_bonus(patterns, figures, sig.direction)
    sig.confidence = min(95, sig.confidence + bonus)
    alert = format_signal_alert(sig, patterns_text)
    return sig, alert


async def db_last_signal_recent(symbol: str, direction: str) -> bool:
    from database import db

    last = await db.last_signal_time(
        symbol, direction, hours=config.SIGNAL_COOLDOWN_HOURS
    )
    return last is not None
