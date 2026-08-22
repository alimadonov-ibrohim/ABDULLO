import html
import math
from datetime import datetime, timezone

import config
from indicators_engine import auto_decimals, fmt_price
from signal_generator import TradingSignal
from utils.i18n import t

BAR_FILLED = "█"
BAR_EMPTY = "░"

_VERDICT_KEYS = {
    "STRONG BUY": "verdict_strong_buy",
    "BUY": "verdict_buy",
    "NEUTRAL": "verdict_neutral",
    "SELL": "verdict_sell",
    "STRONG SELL": "verdict_strong_sell",
}


def esc(text) -> str:
    return html.escape(str(text), quote=False)


def progress_bar(percent: float, width: int = 12) -> str:
    percent = max(0.0, min(100.0, percent))
    filled = int(round(width * percent / 100.0))
    return BAR_FILLED * filled + BAR_EMPTY * (width - filled)


def direction_badge(direction: str, lang: str = "uz") -> str:
    labels = {
        "LONG": {
            "uz": "🟢 LONG (XARID)",
            "ru": "🟢 LONG (ПОКУПКА)",
            "en": "🟢 LONG (BUY)",
        },
        "SHORT": {
            "uz": "🔴 SHORT (SAVDO)",
            "ru": "🔴 SHORT (ПРОДАЖА)",
            "en": "🔴 SHORT (SELL)",
        },
        "NEUTRAL": {"uz": "⚪️ NEYTRAL", "ru": "⚪️ НЕЙТРАЛЬНО", "en": "⚪️ NEUTRAL"},
    }
    return labels.get(direction, {}).get(lang) or labels.get(direction, {}).get(
        "uz", esc(direction)
    )


def verdict_icon(verdict: str) -> str:
    return {
        "STRONG BUY": "🟢🟢",
        "BUY": "🟢",
        "NEUTRAL": "⚪️",
        "SELL": "🔴",
        "STRONG SELL": "🔴🔴",
    }.get(verdict, "⚫️")


def verdict_text(verdict: str, lang: str = "uz") -> str:
    key = _VERDICT_KEYS.get(verdict)
    return t(lang, key) if key else verdict


def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def format_mtf_lines(snapshots: dict, lang: str = "uz") -> list[str]:
    order = [tf for tf in config.TIMEFRAMES if tf in snapshots]
    lines = []
    for tf in order:
        snap = snapshots[tf]
        label = config.TF_LABELS.get(tf, tf)
        icon = verdict_icon(snap.verdict)
        rsi = f"{snap.rsi:.1f}" if snap.rsi is not None else "-"
        macd_state = "-"
        if snap.macd is not None and snap.macd_signal is not None:
            key = "bull_state" if snap.macd > snap.macd_signal else "bear_state"
            macd_state = t(lang, key)
        adx = f"{snap.adx:.1f}" if snap.adx is not None else "-"
        lines.append(
            f"<b>{label}:</b> [{progress_bar(abs(snap.score), 8)}] {icon} "
            f"<b>{verdict_text(snap.verdict, lang)}</b> ({snap.score:+d}) · "
            f"RSI {rsi} · MACD {macd_state} · ADX {adx}"
        )
    return lines


def _risk_block(sl_percent: float, confidence: int, lang: str = "uz") -> list[str]:
    max_risk = config.MAX_RISK_PERCENT
    if sl_percent > 0 and not math.isnan(sl_percent):
        size_pct = round(min(max_risk / sl_percent * 100, 25.0), 1)
        size_usd = f"${100_000 * size_pct / 100:,.0f}"
        size_line = t(lang, "position_size_line", pct=size_pct, usd=size_usd)
    else:
        size_line = t(lang, "size_calc_line")
    quality_key = (
        "quality_high"
        if confidence >= 75
        else "quality_mid"
        if confidence >= 60
        else "quality_low"
    )
    quality = t(lang, quality_key)
    return [
        t(lang, "risk_mgmt_title"),
        t(lang, "risk_max_line", risk=config.MAX_RISK_PERCENT),
        size_line,
        t(lang, "signal_quality_lbl", quality=quality),
    ]


def format_signal_message(
    sig: TradingSignal,
    mtf_lines: list[str],
    patterns_text: str,
    lang: str = "uz",
) -> str:
    badge = direction_badge(sig.direction, lang)
    bar = progress_bar(sig.confidence, 14)

    lines = [
        f"🚀 <b>{esc(sig.title)}</b>  <i>({esc(sig.symbol)} · {esc(sig.exchange)})</i>",
        f"🕒 {utc_now_str()}",
        "",
        f"📊 <b>{t(lang, 'overall_verdict')}:</b> <b>{badge}</b>",
        f"[{bar}] {t(lang, 'confidence_lbl')}: <b>{sig.confidence}%</b> ({t(lang, 'winrate_lbl')})",
        f"<i>{t(lang, 'combined_score_lbl')}: {sig.combined_score:+.1f}/100"
        + (f" · ADX(4H): {sig.adx_4h:.1f}" if sig.adx_4h is not None else "")
        + "</i>",
        "",
        t(lang, "mtf_title"),
    ]
    lines.extend(f"  {line}" for line in mtf_lines)

    if patterns_text:
        lines += ["", t(lang, "patterns_line", patterns=patterns_text)]

    if sig.resistances or sig.supports:
        res_txt = fmt_price(sig.resistances[0], sig.decimals) if sig.resistances else "-"
        sup_txt = fmt_price(sig.supports[0], sig.decimals) if sig.supports else "-"
        lines += [
            "",
            t(lang, "levels_title"),
            f"  {t(lang, 'near_resistance')}: <code>{res_txt}</code>",
            f"  {t(lang, 'near_support')}: <code>{sup_txt}</code>",
        ]

    arrow = "📈" if sig.direction == "LONG" else "📉"
    tp_pct1 = abs((sig.tp1 - sig.entry) / sig.entry) * 100
    tp_pct2 = abs((sig.tp2 - sig.entry) / sig.entry) * 100
    tp_pct3 = abs((sig.tp3 - sig.entry) / sig.entry) * 100

    lines += [
        "",
        f"{arrow} <b>{t(lang, 'trade_plan')}</b>",
        f"💰 <b>{t(lang, 'entry_lbl')}:</b> <code>{fmt_price(sig.entry, sig.decimals)}</code>",
        f"🛑 <b>{t(lang, 'sl_lbl')}:</b> <code>{fmt_price(sig.sl, sig.decimals)}</code> (-{sig.sl_percent:.2f}%)",
        f"✅ <b>TP1:</b> <code>{fmt_price(sig.tp1, sig.decimals)}</code> (+{tp_pct1:.2f}%) | RR 1:1",
        f"✅ <b>TP2:</b> <code>{fmt_price(sig.tp2, sig.decimals)}</code> (+{tp_pct2:.2f}%) | RR 1:2",
        f"✅ <b>TP3:</b> <code>{fmt_price(sig.tp3, sig.decimals)}</code> (+{tp_pct3:.2f}%) | RR 1:3",
        f"⚖️ {t(lang, 'rr_total_lbl')}: <b>1:{sig.rr_ratio:.0f}</b>",
        "",
    ]
    lines.extend(_risk_block(sig.sl_percent, sig.confidence, lang))
    lines += [
        "",
        t(lang, "disclaimer"),
    ]
    return "\n".join(lines)


def format_neutral_summary(
    result, mtf_lines: list[str], patterns_text: str, lang: str = "uz"
) -> str:
    dec = auto_decimals(result.last_price)
    price = fmt_price(result.last_price, dec)
    lines = [
        f"📊 <b>{esc(result.title)}</b>  <i>({esc(result.symbol)} · {esc(result.exchange)})</i>",
        f"🕒 {utc_now_str()}",
        "",
        t(lang, "neutral_zone"),
        f"<i>{t(lang, 'combined_score_lbl')}: {result.combined_score:+.1f}/100</i>",
        t(
            lang,
            "strength_line",
            bar=progress_bar(abs(result.combined_score), 14),
            score=min(abs(int(result.combined_score)), 100),
        ),
        "",
        t(lang, "mtf_title"),
    ]
    lines.extend(f"  {line}" for line in mtf_lines)
    if patterns_text:
        lines += ["", t(lang, "patterns_line", patterns=patterns_text)]
    lines += [
        "",
        t(lang, "signals_hint"),
        t(lang, "disclaimer"),
        f"💰 {t(lang, 'current_price')}: <code>{price}</code>",
    ]
    return "\n".join(lines)


def format_signal_alert(
    sig: TradingSignal, patterns_text: str, lang: str = "uz"
) -> str:
    badge = direction_badge(sig.direction, lang)
    arrow = "📈" if sig.direction == "LONG" else "📉"
    header = t(lang, "auto_header", title=esc(sig.title))
    return "\n".join(
        [
            header,
            f"<i>{esc(sig.symbol)} · {esc(sig.exchange)} · Multi-TF</i>",
            "",
            f"{arrow} <b>{badge}</b>",
            f"[{progress_bar(sig.confidence, 14)}] Winrate: <b>{sig.confidence}%</b>",
            "",
            f"💰 Entry: <code>{fmt_price(sig.entry, sig.decimals)}</code>",
            f"🛑 SL: <code>{fmt_price(sig.sl, sig.decimals)}</code> (-{sig.sl_percent:.2f}%)",
            f"✅ TP1: <code>{fmt_price(sig.tp1, sig.decimals)}</code> | TP2: <code>{fmt_price(sig.tp2, sig.decimals)}</code> | TP3: <code>{fmt_price(sig.tp3, sig.decimals)}</code>",
            f"⚖️ RR: <b>1:{sig.rr_ratio:.0f}</b>",
            f"💼 {t(lang, 'risk_deposit_lbl')}: ≤{config.MAX_RISK_PERCENT}%",
            "",
            f"🕯 {patterns_text}" if patterns_text else "",
            f"🕒 {utc_now_str()} · <i>{t(lang, 'not_advice_short')}</i>",
        ]
    )
