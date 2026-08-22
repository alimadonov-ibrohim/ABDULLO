"""
Vercel serverless kirish nuqtasi.
/webhook - Telegram webhook (foydalanuvchi xablari uchun)
/check   - Bir martalik signal tekshiruvi (cron urib turadi)
"""
from fastapi import FastAPI, Request, HTTPException, Query

import config
from data_fetcher import DataFetcher
from telegram_notifier import TelegramNotifier
from main import run_check_cycle, process_update

app = FastAPI()

_last_signal_time = {}


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    try:
        process_update(payload, notifier)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


@app.get("/check")
async def check(key: str = Query(default=""), force: bool = Query(default=False)):
    if config.CHECK_SECRET and key != config.CHECK_SECRET:
        raise HTTPException(status_code=403, detail="Noto'g'ri kalit")
    fetcher = DataFetcher(config.TWELVE_DATA_API_KEY)
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    sent = run_check_cycle(fetcher, notifier, _last_signal_time, ignore_weekend=force)
    return {"ok": True, "sent": sent}
