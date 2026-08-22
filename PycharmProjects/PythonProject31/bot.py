import asyncio
import contextlib

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from database import db
from handlers import get_routers
from logger import get_logger, setup_logging
from middlewares.ban import BanMiddleware
from scheduler import start_scanner, stop_scanner

log = get_logger("bot")

COMMANDS = [
    BotCommand(command="start", description="🚀 Menyuni ochish"),
    BotCommand(command="menu", description="🎛 Asosiy menyu"),
    BotCommand(command="vip", description="💎 VIP obuna"),
    BotCommand(command="stats", description="📈 Statistika"),
    BotCommand(command="info", description="📚 Bot ma'lumotlari"),
    BotCommand(command="creator", description="👑 Yaratuvchi"),
    BotCommand(command="clear", description="🧹 Chatni tozalash"),
]

PLACEHOLDER_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

STARTUP_RETRIES = 8
RETRY_DELAY_SEC = 5


async def _with_retries(coro_factory, what: str):
    """Tarmoq beqaror bo'lsa bir necha marta qayta urinadi."""
    last_exc: Exception | None = None
    for attempt in range(1, STARTUP_RETRIES + 1):
        try:
            return await coro_factory()
        except TelegramNetworkError as exc:
            last_exc = exc
            log.warning(
                "%s urinish %d/%d muvaffaqiyatsiz (%s) — %ds dan keyin qayta...",
                what,
                attempt,
                STARTUP_RETRIES,
                type(exc).__name__,
                RETRY_DELAY_SEC,
            )
            await asyncio.sleep(RETRY_DELAY_SEC)
    raise last_exc


async def main() -> None:
    setup_logging()

    if not config.BOT_TOKEN or config.BOT_TOKEN == PLACEHOLDER_TOKEN:
        log.critical("BOT_TOKEN sozlanmagan! .env faylini to'ldiring.")
        raise SystemExit(2)
    if not config.ADMIN_IDS:
        log.warning("ADMIN_IDS bo'sh — admin buyruqlari ishlamaydi.")

    session = AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    for router in get_routers():
        dp.include_router(router)

    ban_mw = BanMiddleware()
    dp.message.outer_middleware(ban_mw)
    dp.callback_query.outer_middleware(ban_mw)

    scanner_task = None
    try:
        await db.connect()
        await _with_retries(lambda: bot.set_my_commands(COMMANDS), "set_my_commands")
        me = await _with_retries(bot.get_me, "get_me")
        log.info(
            "Bot @%s sifatida ishga tushdi (%s juftlik, VIP kanal: %s)",
            me.username,
            len(config.ALL_SYMBOLS),
            config.CHANNEL_ID or "o'chirilgan",
        )
        scanner_task = start_scanner(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception:
        log.exception("Fatal xatolik — bot to'xtatildi")
        raise
    finally:
        await stop_scanner(scanner_task)
        await db.close()
        with contextlib.suppress(Exception):
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        raise SystemExit(code)
