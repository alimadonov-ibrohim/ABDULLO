import re

import config
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database import db
from logger import get_logger
from services import full_analysis
from utils.formatters import esc, utc_now_str
from utils.i18n import get_lang, t
from utils.keyboards import after_analysis, back_to_main, history_back, pairs_menu
from utils.market_hours import is_weekend_utc

log = get_logger("handlers.analysis")

router = Router(name="analysis")

SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{5,15}$")


class CustomPairState(StatesGroup):
    waiting_symbol = State()


async def pairs_menu_content(lang: str = "uz") -> tuple[str, object]:
    note = t(lang, "weekend_note") if is_weekend_utc() else ""
    text = t(lang, "pairs_menu_text", note=note)
    return text, pairs_menu(lang).as_markup()


@router.callback_query(F.data == "pairs:list")
async def show_pairs(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    text, markup = await pairs_menu_content(lang)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


async def history_content(lang: str = "uz") -> tuple[str, object]:
    rows = await db.recent_signals(limit=10)
    if not rows:
        return t(lang, "history_empty"), history_back(lang).as_markup()

    lines = [t(lang, "history_title")]
    for r in rows:
        icon = "⚡️" if r["source"] == "auto" else "👤"
        arrow = "🟢" if r["direction"] == "LONG" else "🔴"
        entry_txt = f"{r['entry']:g}" if r["entry"] else "-"
        sl_txt = f"{r['sl']:g}" if r["sl"] else "-"
        conf = int(r["confidence"]) if r["confidence"] is not None else "-"
        lines.append(
            f"{icon} {arrow} <b>{esc(r['symbol'])}</b> · {conf}% · "
            f"E: {entry_txt} · SL: {sl_txt} · <i>{r['created_at']}</i>"
        )
    lines.append(f"\n🕒 {utc_now_str()}")
    return "\n".join(lines), history_back(lang).as_markup()


@router.callback_query(F.data == "history:list")
async def show_history(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    text, markup = await history_content(lang)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


async def _market_closed(message: Message, lang: str):
    await message.answer(
        t(lang, "market_closed"), reply_markup=back_to_main(lang).as_markup()
    )


async def _run_analysis(
    message: Message, symbol: str, user_id: int | None = None, lang: str = "uz"
):
    try:
        await message.edit_text(
            t(lang, "analyzing_placeholder", sym=esc(symbol))
        )
    except Exception:
        log.warning("placeholder edit failed for %s", symbol)

    try:
        meta = config.get_pair_meta(symbol) or config.guess_pair_meta(symbol)
        text, result, sig = await full_analysis(symbol, meta=meta, lang=lang)
        if sig:
            await db.save_signal(
                {
                    "user_id": user_id,
                    "symbol": result.symbol,
                    "direction": result.direction,
                    "timeframe": "+".join(config.TIMEFRAMES),
                    "entry": sig.entry,
                    "sl": sig.sl,
                    "tp1": sig.tp1,
                    "tp2": sig.tp2,
                    "tp3": sig.tp3,
                    "confidence": sig.confidence,
                    "rr_ratio": sig.rr_ratio,
                    "source": "manual",
                }
            )
        if user_id:
            await db.increment_requests(user_id)
        await message.edit_text(
            text, reply_markup=after_analysis(result.symbol, lang).as_markup()
        )
    except Exception:
        log.exception("analysis failed for %s", symbol)
        await message.edit_text(
            t(lang, "analysis_failed", sym=esc(symbol)),
            reply_markup=back_to_main(lang).as_markup(),
        )


@router.callback_query(F.data.startswith("analyze:"))
async def cb_analyze(cb: CallbackQuery, state: FSMContext):
    symbol = cb.data.split(":", 1)[1].upper()
    lang = await get_lang(cb.from_user.id)
    if is_weekend_utc():
        await cb.message.answer(
            t(lang, "market_closed"), reply_markup=back_to_main(lang).as_markup()
        )
        await cb.answer()
        return
    await cb.answer(t(lang, "analyzing_cb"))
    await _run_analysis(cb.message, symbol, user_id=cb.from_user.id, lang=lang)


@router.callback_query(F.data.startswith("refresh:"))
async def cb_refresh(cb: CallbackQuery):
    symbol = cb.data.split(":", 1)[1].upper()
    lang = await get_lang(cb.from_user.id)
    if is_weekend_utc():
        await cb.message.answer(
            t(lang, "market_closed"), reply_markup=back_to_main(lang).as_markup()
        )
        await cb.answer()
        return
    await cb.answer(t(lang, "refreshing_cb"))
    await _run_analysis(cb.message, symbol, user_id=cb.from_user.id, lang=lang)


@router.callback_query(F.data == "pairs:custom")
async def cb_custom_pair(cb: CallbackQuery, state: FSMContext):
    lang = await get_lang(cb.from_user.id)
    await state.set_state(CustomPairState.waiting_symbol)
    await cb.message.edit_text(
        t(lang, "custom_prompt"),
        reply_markup=back_to_main(lang).as_markup(),
    )
    await cb.answer()


@router.message(CustomPairState.waiting_symbol, F.text)
async def receive_custom_symbol(message: Message, state: FSMContext):
    raw = (message.text or "").strip().upper()
    await state.clear()
    lang = await get_lang(message.from_user.id)

    if not SYMBOL_RE.match(raw):
        await message.answer(
            t(lang, "invalid_symbol"),
            reply_markup=pairs_menu(lang).as_markup(),
        )
        return

    if is_weekend_utc():
        await _market_closed(message, lang)
        return

    placeholder = await message.answer(t(lang, "analyzing_simple", sym=esc(raw)))
    await _run_analysis(placeholder, raw, user_id=message.from_user.id, lang=lang)
