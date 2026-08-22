import asyncio
import contextlib

from aiogram.exceptions import TelegramNetworkError

import config
from database import db
from logger import get_logger, setup_logging
from main import COMMANDS, ensure_token
from scheduler import start_scanner, stop_scanner

log = get_logger("bot")

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

    if not ensure_token():
        log.critical("BOT_TOKEN sozlanmagan! .env faylini to'ldiring.")
        raise SystemExit(2)
    if not config.ADMIN_IDS:
        log.warning("ADMIN_IDS bo'sh — admin buyruqlari ishlamaydi.")

    from main import build_bot, build_dispatcher

    bot = build_bot()
    dp = build_dispatcher()

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
