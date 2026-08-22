import asyncio
from datetime import datetime

import config
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from database import db
from logger import get_logger
from services import auto_scan_symbol
from utils.market_hours import is_weekend_utc

log = get_logger("scheduler")

_scan_lock = asyncio.Lock()
_last_weekend_skip: str | None = None


async def _send_safe(bot: Bot, chat_id: int, text: str) -> bool:
    for attempt in range(3):
        try:
            await bot.send_message(chat_id, text)
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            log.info("User %s blocked the bot", chat_id)
            return False
        except Exception:
            log.exception("send failed to %s (attempt %s)", chat_id, attempt + 1)
            await asyncio.sleep(2 * (attempt + 1))
    return False


async def run_scan_cycle(bot: Bot) -> int:
    async with _scan_lock:
        sent = 0
        vip_ids = await db.active_vip_user_ids()
        channel_id = config.CHANNEL_ID

        for symbol in config.ALL_SYMBOLS:
            try:
                sig, alert = await auto_scan_symbol(symbol)
            except Exception:
                log.exception("scan failed for %s", symbol)
                continue

            if not sig or not alert:
                continue

            if sig.confidence < config.AUTO_SIGNAL_MIN_CONFIDENCE:
                log.debug(
                    "%s %s skipped (%s%% < %s%%)",
                    sig.symbol,
                    sig.direction,
                    sig.confidence,
                    config.AUTO_SIGNAL_MIN_CONFIDENCE,
                )
                continue

            try:
                await db.save_signal(
                    {
                        "user_id": None,
                        "symbol": sig.symbol,
                        "direction": sig.direction,
                        "timeframe": "+".join(config.TIMEFRAMES),
                        "entry": sig.entry,
                        "sl": sig.sl,
                        "tp1": sig.tp1,
                        "tp2": sig.tp2,
                        "tp3": sig.tp3,
                        "confidence": sig.confidence,
                        "rr_ratio": sig.rr_ratio,
                        "source": "auto",
                    }
                )
            except Exception:
                log.exception("save_signal failed for %s", sig.symbol)

            log.info(
                "AUTO SIGNAL %s %s conf=%s entry=%s",
                sig.symbol,
                sig.direction,
                sig.confidence,
                sig.entry,
            )

            if channel_id:
                if await _send_safe(bot, int(channel_id), alert):
                    sent += 1

            for uid in vip_ids:
                if await _send_safe(bot, uid, alert):
                    sent += 1
                await asyncio.sleep(0.05)

        return sent


async def scanner_loop(bot: Bot) -> None:
    global _last_weekend_skip
    interval_sec = max(5, config.SCAN_INTERVAL_MINUTES) * 60
    log.info(
        "Scanner started: every %s min, min confidence %s%%, pairs: %s",
        config.SCAN_INTERVAL_MINUTES,
        config.AUTO_SIGNAL_MIN_CONFIDENCE,
        ", ".join(config.ALL_SYMBOLS),
    )
    while True:
        started = datetime.now()
        if is_weekend_utc(started):
            today = started.strftime("%Y-%m-%d")
            if _last_weekend_skip != today:
                _last_weekend_skip = today
                log.info("Weekend (shanba/yakshanba) — avto-skaner to'xtatildi")
        else:
            try:
                count = await run_scan_cycle(bot)
                if count:
                    log.info("Scan cycle sent %s messages", count)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Scan cycle crashed; continuing")
        elapsed = (datetime.now() - started).total_seconds()
        sleep_for = max(30, interval_sec - elapsed)
        await asyncio.sleep(sleep_for)


def start_scanner(bot: Bot) -> asyncio.Task:
    return asyncio.create_task(scanner_loop(bot), name="market-scanner")


async def stop_scanner(task: asyncio.Task | None) -> None:
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
