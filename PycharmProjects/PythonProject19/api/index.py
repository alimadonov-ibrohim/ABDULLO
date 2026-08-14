import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from main import BOT_TOKEN, bot, dp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

WEBHOOK_PATH = "/api/webhook"

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    vercel_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")
    if vercel_url:
        url = os.getenv("WEBHOOK_URL") or f"https://{vercel_url}{WEBHOOK_PATH}"
        await bot.set_webhook(url)
        logging.info("Webhook set: %s", url)
    else:
        logging.warning("VERCEL_PROJECT_PRODUCTION_URL topilmadi, webhook o'rnatilmadi")
    yield
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"ok": True, "name": "Tabrik Bot", "token_set": bool(BOT_TOKEN)}


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    asyncio.create_task(dp.feed_update(bot, update))
    return {"ok": True}
