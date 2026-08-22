import config
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from database import db
from logger import get_logger
from utils.i18n import cache_lang, t

log = get_logger("middlewares.ban")


class BanMiddleware(BaseMiddleware):
    """Bloklangan foydalanuvchilarni har qanday handlerdan oldin to'sadi."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user is None or user.is_bot:
            return await handler(event, data)

        if user.id in config.ADMIN_IDS:
            return await handler(event, data)

        info = await db.get_user(user.id)
        lang = None
        if info:
            lang = info.get("language")
            cache_lang(user.id, lang)
            if not info.get("is_banned"):
                data["lang"] = lang or "uz"
                return await handler(event, data)
        else:
            data["lang"] = "uz"
            return await handler(event, data)

        # Bloklangan yoki til ma'lum — blok xabarini yuboramiz
        try:
            if isinstance(event, CallbackQuery):
                await event.answer(t(lang, "banned_msg"), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(t(lang, "banned_msg"))
        except Exception:
            log.exception("ban notice failed for %s", user.id)
        return  # handler chaqirilmaydi — to'liq blok
