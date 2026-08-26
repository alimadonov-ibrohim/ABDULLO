import config
import indicators_engine
import pattern_scanner
import price_action
import signal_generator
from logger import get_logger
from utils.formatters import (
    format_mtf_lines,
    format_neutral_summary,
    format_signal_alert,
    format_signal_message,
)
from utils.i18n import t

log = get_logger("services")


async def full_analysis(symbol: str, meta: dict | None = None, lang: str = "uz"):
    result = await indicators_engine.analyze_symbol(symbol, meta=meta)

    # TradingView javob bermasa — soxta 'neytral' emas, halol xabar beramiz
    if result.tv_ok == 0:
        return t(lang, "tv_unavailable"), result, None

    patterns = pattern_scanner.scan_candle_patterns(result.ohlc)
    figures = pattern_scanner.scan_chart_figures(result.ohlc)
    patterns_text = pattern_scanner.summarize_patterns(patterns, figures, lang)

    pa = price_action.scan_price_action(result.ohlc)
    pa_txt = price_action.pa_text(pa, lang)

    sig = signal_generator.generate_signal(result, patterns, figures)
    if sig and pa:
        sig.confidence = min(95, sig.confidence + price_action.price_action_bonus(pa, sig.direction))

    mtf_lines = format_mtf_lines(result.snapshots, lang)

    if sig:
        text = format_signal_message(sig, mtf_lines, patterns_text, lang, pa_text=pa_txt)
    else:
        text = format_neutral_summary(
            result, mtf_lines, patterns_text, lang, pa_text=pa_txt
        )
    return text, result, sig


async def auto_scan_symbol(symbol: str):
    meta = config.get_pair_meta(symbol)
    if not meta:
        return None, None

    result = await indicators_engine.analyze_symbol(symbol, meta=meta)
    if result.tv_ok == 0:
        log.warning("Scan %s skipped — TradingView javob bermadi", symbol)
        return None, result
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

    pa = price_action.scan_price_action(result.ohlc)
    if pa:
        sig.confidence = min(95, sig.confidence + price_action.price_action_bonus(pa, sig.direction))
    alert = format_signal_alert(sig, patterns_text)
    return sig, alert


async def db_last_signal_recent(symbol: str, direction: str) -> bool:
    from database import db

    last = await db.last_signal_time(
        symbol, direction, hours=config.SIGNAL_COOLDOWN_HOURS
    )
    return last is not None
