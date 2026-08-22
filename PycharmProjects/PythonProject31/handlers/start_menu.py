import asyncio
import contextlib

import config
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from database import db
from logger import get_logger
from utils.formatters import esc, progress_bar
from utils.i18n import SUPPORTED_LANGS, cache_lang, get_lang, t
from utils.keyboards import back_to_main, lang_keyboard, main_menu

log = get_logger("handlers.start")

router = Router(name="start_menu")

_LANG_BTN = {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"}
_CREATOR_BTN = {
    "uz": "👑 Yaratuvchi",
    "ru": "👑 Создатель",
    "en": "👑 Creator",
}

_REPLY_ACTIONS: dict[str, str] = {}
for _lang in SUPPORTED_LANGS:
    _REPLY_ACTIONS[t(_lang, "btn_analysis")] = "pairs:list"
    _REPLY_ACTIONS[t(_lang, "btn_vip")] = "menu:vip"
    _REPLY_ACTIONS[t(_lang, "btn_history")] = "history:list"
    _REPLY_ACTIONS[t(_lang, "btn_stats")] = "menu:stats"
    _REPLY_ACTIONS[t(_lang, "btn_help")] = "menu:help"
    _REPLY_ACTIONS[t(_lang, "btn_info")] = "menu:info"
    _REPLY_ACTIONS[t(_lang, "btn_clear")] = "chat:clear"
    _REPLY_ACTIONS[_LANG_BTN[_lang]] = "lang:open"
    _REPLY_ACTIONS[_CREATOR_BTN[_lang]] = "menu:creator"

_CLEAR_DEPTH = 60


def reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=t(lang, "btn_analysis")), KeyboardButton(text=t(lang, "btn_vip"))],
        [
            KeyboardButton(text=t(lang, "btn_history")),
            KeyboardButton(text=t(lang, "btn_stats")),
        ],
        [KeyboardButton(text=t(lang, "btn_help")), KeyboardButton(text=t(lang, "btn_info"))],
        [KeyboardButton(text=_LANG_BTN.get(lang, _LANG_BTN["uz"])), KeyboardButton(text=_CREATOR_BTN.get(lang, _CREATOR_BTN["uz"]))],
        [KeyboardButton(text=t(lang, "btn_clear"))],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def send_main(target, name: str | None = None, lang: str = "uz"):
    await target.answer(
        t(lang, "welcome", name=esc(name or "trader")),
        reply_markup=reply_keyboard(lang),
    )


async def ask_language(target):
    await target.answer(
        t(None, "choose_lang"), reply_markup=lang_keyboard().as_markup()
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        await db.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    except Exception:
        log.exception("upsert_user failed")

    chosen = None
    try:
        chosen = await db.get_language(message.from_user.id)
    except Exception:
        log.exception("get_language failed")
    if not chosen:
        await ask_language(message)
        return
    cache_lang(message.from_user.id, chosen)
    await send_main(message, message.from_user.first_name, chosen)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(
        t(lang, "welcome", name=esc(message.from_user.first_name or "trader")),
        reply_markup=main_menu(
            lang,
            is_admin=message.from_user.id in config.ADMIN_IDS,
        ).as_markup(),
    )


@router.message(Command("creator"))
async def cmd_creator(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "creator_text"), reply_markup=back_to_main(lang).as_markup())


@router.message(Command("info"))
async def cmd_info(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "info_text"), reply_markup=back_to_main(lang).as_markup())


@router.message(Command("clear"))
async def cmd_clear(message: Message, state: FSMContext):
    await _clear_chat(message, state)


async def _clear_chat(message: Message, state: FSMContext | None = None) -> None:
    lang = await get_lang(message.from_user.id)
    if state is not None:
        await state.clear()
    chat_id = message.chat.id
    base = message.message_id
    deleted = 0
    for msg_id in range(base, max(base - _CLEAR_DEPTH, 0), -1):
        try:
            await message.bot.delete_message(chat_id, msg_id)
            deleted += 1
        except TelegramBadRequest:
            continue
        except Exception:
            break
        finally:
            await asyncio.sleep(0.05)
    with contextlib.suppress(Exception):
        await message.answer(t(lang, "clear_done", n=deleted))
    await send_main(message, message.from_user.first_name, lang)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(
        await stats_text(lang), reply_markup=back_to_main(lang).as_markup()
    )


async def stats_text(lang: str = "uz") -> str:
    s = await db.stats_summary()
    total_signals = s["total_signals"]
    longs = s["buy"]
    shorts = s["sell"]

    lines = [
        t(lang, "stats_title"),
        "",
        t(lang, "stats_users", n=s["total_users"]),
        t(lang, "stats_today", n=s["today_signals"]),
        "",
        t(lang, "stats_total", n=total_signals),
        t(lang, "stats_long_short", long=longs, short=shorts),
    ]
    if total_signals:
        lp = progress_bar(longs * 100 / total_signals, 12)
        lines.append(
            t(
                lang,
                "stats_long_share",
                bar=lp,
                pct=longs * 100 // max(total_signals, 1),
            )
        )
    if s["top_symbols"]:
        lines.append(t(lang, "stats_top"))
        for sym, cnt in s["top_symbols"].items():
            lines.append(f"  • {esc(sym)} — {cnt}")
    if s["avg_confidence"]:
        lines.append(t(lang, "stats_avg_conf", pct=f"{s['avg_confidence']:.0f}"))
    return "\n".join(lines)


@router.callback_query(F.data == "menu:main")
async def cb_main(cb):
    lang = await get_lang(cb.from_user.id)
    try:
        await cb.message.edit_text(
            t(lang, "welcome", name=esc(cb.from_user.first_name or "trader")),
            reply_markup=main_menu(
                lang, is_admin=cb.from_user.id in config.ADMIN_IDS
            ).as_markup(),
        )
    except TelegramBadRequest:
        pass
    await cb.answer()


@router.callback_query(F.data == "lang:menu")
async def cb_lang_menu(cb):
    await cb.message.edit_text(
        t(None, "choose_lang"), reply_markup=lang_keyboard().as_markup()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("lang:set:"))
async def cb_lang_set(cb):
    code = cb.data.rsplit(":", 1)[-1]
    if code not in SUPPORTED_LANGS:
        code = "uz"
    try:
        await db.set_language(cb.from_user.id, code)
    except Exception:
        log.exception("set_language failed")
    cache_lang(cb.from_user.id, code)
    await cb.answer(t(code, "lang_changed"))
    await send_main(cb.message, cb.from_user.first_name, code)


@router.callback_query(F.data == "menu:creator")
async def cb_creator(cb):
    lang = await get_lang(cb.from_user.id)
    await cb.message.edit_text(
        t(lang, "creator_text"), reply_markup=back_to_main(lang).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(cb):
    lang = await get_lang(cb.from_user.id)
    await cb.message.edit_text(
        t(lang, "help_text"), reply_markup=back_to_main(lang).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "menu:info")
async def cb_info(cb):
    lang = await get_lang(cb.from_user.id)
    await cb.message.edit_text(
        t(lang, "info_text"), reply_markup=back_to_main(lang).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "menu:stats")
async def cb_stats(cb):
    lang = await get_lang(cb.from_user.id)
    await cb.message.edit_text(
        await stats_text(lang), reply_markup=back_to_main(lang).as_markup()
    )
    await cb.answer()


@router.message(F.text.in_(_REPLY_ACTIONS))
async def reply_shortcuts(message: Message, state: FSMContext):
    from .analysis import history_content, pairs_menu_content
    from .vip import vip_info_content

    lang = await get_lang(message.from_user.id)
    key = _REPLY_ACTIONS[message.text.strip()]
    if key == "pairs:list":
        text, markup = await pairs_menu_content(lang)
        await message.answer(text, reply_markup=markup)
    elif key == "history:list":
        await message.answer(*await history_content(lang))
    elif key == "menu:vip":
        text, markup = await vip_info_content(message.from_user.id, lang)
        await message.answer(text, reply_markup=markup)
    elif key == "menu:stats":
        await message.answer(
            await stats_text(lang), reply_markup=back_to_main(lang).as_markup()
        )
    elif key == "chat:clear":
        await _clear_chat(message, state)
    elif key == "lang:open":
        await message.answer(
            t(None, "choose_lang"), reply_markup=lang_keyboard().as_markup()
        )
    elif key == "menu:creator":
        await message.answer(
            t(lang, "creator_text"), reply_markup=back_to_main(lang).as_markup()
        )
    elif key == "menu:info":
        await message.answer(
            t(lang, "info_text"), reply_markup=back_to_main(lang).as_markup()
        )
    else:
        await message.answer(
            t(lang, "help_text"), reply_markup=back_to_main(lang).as_markup()
        )
