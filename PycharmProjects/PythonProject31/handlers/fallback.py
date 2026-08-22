from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from utils.i18n import get_lang, t

router = Router(name="fallback")


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "fallback_unknown_cmd"))


@router.message(F.text)
async def fallback_text(message: Message):
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "fallback_text"))


@router.callback_query()
async def unknown_callback(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    await cb.answer(t(lang, "unknown_callback_alert"), show_alert=True)
