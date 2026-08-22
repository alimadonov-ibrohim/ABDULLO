"""
Vercel serverless kirish nuqtasi.

  POST /webhook  — Telegram webhook (foydalanuvchi xabarlari)
  GET  /setup    — webhookni o'rnatish (deploydan keyin BIR MARTA ochiladi)
  GET  /check    — avto-skaner sikli (Vercel Cron urib turadi)
  GET  /         — health check

Vercel serverless har bir so'rov alohida event loop da ishlaydi —
shu sababli bot/dispatcher va DB har chaqiruvda yangi qurilib, oxirida yopiladi.
"""

from fastapi import FastAPI, HTTPException, Query, Request

import config
from database import db
from logger import get_logger
from main import COMMANDS, build_bot, build_dispatcher, ensure_token
from scheduler import run_scan_cycle

log = get_logger("vercel")

app = FastAPI(title="Forex & Crypto Analytics Bot")


def _check_secret(request: Request, key: str) -> None:
    # Vercel Cron so'rovlari x-vercel-cron headeri bilan keladi
    if request.headers.get("x-vercel-cron") == "1":
        return
    if config.CHECK_SECRET and key != config.CHECK_SECRET:
        raise HTTPException(status_code=403, detail="Noto'g'ri kalit")
    if not config.CHECK_SECRET and not key:
        raise HTTPException(status_code=403, detail="CHECK_SECRET sozlanmagan")


@app.get("/")
async def root():
    return {"ok": True, "service": "forex-crypto-analytics-bot"}


@app.post("/webhook")
async def webhook(request: Request):
    if config.WEBHOOK_SECRET:
        got = request.headers.get("x-telegram-bot-api-secret-token", "")
        if got != config.WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Bad secret token")

    if not ensure_token():
        raise HTTPException(status_code=500, detail="BOT_TOKEN sozlanmagan")

    from aiogram.types import Update

    payload = await request.json()
    bot = build_bot()
    dp = build_dispatcher()
    try:
        await db.connect()
        update = Update.model_validate(payload, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        await db.close()
        try:
            await bot.session.close()
        except Exception:
            pass
    return {"ok": True}


@app.get("/setup")
async def setup(request: Request, key: str = Query(default="")):
    _check_secret(request, key)

    base = request.headers.get("x-forwarded-host") or request.url.netloc
    proto = request.headers.get("x-forwarded-proto", "https")
    url = f"{proto}://{base}/webhook"

    bot = build_bot()
    try:
        await bot.set_webhook(
            url,
            secret_token=config.WEBHOOK_SECRET or None,
            drop_pending_updates=True,
            allowed_updates=dp_allowed_updates(),
        )
        await bot.set_my_commands(COMMANDS)
    finally:
        try:
            await bot.session.close()
        except Exception:
            pass
    return {"ok": True, "webhook": url}


@app.get("/check")
async def check(
    request: Request,
    key: str = Query(default=""),
    force: bool = Query(default=False),
):
    _check_secret(request, key)

    from utils.market_hours import is_weekend_utc

    if not force and is_weekend_utc():
        return {"ok": True, "sent": 0, "note": "weekend - bozor yopiq"}

    bot = build_bot()
    try:
        await db.connect()
        sent = await run_scan_cycle(bot)
    finally:
        await db.close()
        try:
            await bot.session.close()
        except Exception:
            pass
    return {"ok": True, "sent": sent}


def dp_allowed_updates() -> list[str]:
    return ["message", "callback_query"]
