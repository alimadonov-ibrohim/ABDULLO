"""Umumiy bot/dispatcher fabrikasi — polling (bot.py) va webhook (vercel_api.py) uchun."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config

PLACEHOLDER_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

COMMANDS = [
    BotCommand(command="start", description="🚀 Menyuni ochish"),
    BotCommand(command="menu", description="🎛 Asosiy menyu"),
    BotCommand(command="vip", description="💎 VIP obuna ($10/oydan)"),
    BotCommand(command="myid", description="🆔 Telegram ID raqamingiz"),
    BotCommand(command="stats", description="📈 Statistika"),
    BotCommand(command="info", description="📚 Bot imkoniyatlari"),
    BotCommand(command="help", description="ℹ️ Yordam va buyruqlar"),
    BotCommand(command="creator", description="👑 Yaratuvchi"),
    BotCommand(command="clear", description="🧹 Chatni tozalash"),
]


def build_bot() -> Bot:
    session = AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None
    return Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


# Vercel warm lambda: routerlar bir marta ulanadi, dispatcher keshlanadi.
# Har chaqiruvda yangi Dispatcher qurilsa — "Router is already attached" 500 beradi.
_dispatcher: Dispatcher | None = None


def build_dispatcher() -> Dispatcher:
    global _dispatcher
    if _dispatcher is not None:
        return _dispatcher

    from handlers import get_routers
    from middlewares.ban import BanMiddleware

    dp = Dispatcher(storage=MemoryStorage())
    for router in get_routers():
        dp.include_router(router)

    ban_mw = BanMiddleware()
    dp.message.outer_middleware(ban_mw)
    dp.callback_query.outer_middleware(ban_mw)
    _dispatcher = dp
    return dp


def ensure_token() -> bool:
    return bool(config.BOT_TOKEN) and config.BOT_TOKEN != PLACEHOLDER_TOKEN
