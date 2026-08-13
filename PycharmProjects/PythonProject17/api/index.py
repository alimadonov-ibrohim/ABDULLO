import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message, Update
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from downloader import MAX_FILE_SIZE, SUPPORTED_RE, cleanup, download_video

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/api/webhook"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Salom! Men video yuklab beruvchi botman.\n\n"
        "Menga Instagram, YouTube, TikTok, Pinterest yoki Facebook havolasini yuboring — "
        "videoni yuklab olib, shu yerga yuboraman! 🎬\n\n"
        "⚠️ Eng katta fayl hajmi: 50 MB"
    )


@dp.message(F.text)
async def handle_link(message: Message):
    url = message.text.strip()
    if not SUPPORTED_RE.search(url):
        await message.answer(
            "❌ Qo'llab-quvvatlanadigan sayt emas.\n"
            "Instagram, YouTube, TikTok, Pinterest, Facebook havolasini yuboring."
        )
        return

    status = await message.answer("⏳ Yuklab olinmoqda, kuting...")
    loop = asyncio.get_running_loop()
    path = None
    try:
        path = await loop.run_in_executor(None, download_video, url)
        size = os.path.getsize(path)
        if size > MAX_FILE_SIZE:
            await status.edit_text("❌ Video 50 MB dan katta, yuborib bo'lmadi.")
            return
        video = FSInputFile(path)
        await message.answer_video(video, caption="✅ Mana videongiz!")
        await status.delete()
    except Exception as e:
        logging.exception("Download failed")
        await status.edit_text(
            f"❌ Yuklab bo'lmadi: {e}\n\n"
            "Sabablari: video maxfiy bo'lishi, sayt cheklovi yoki noto'g'ri havola."
        )
    finally:
        if path:
            loop.run_in_executor(None, cleanup, path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    url = os.getenv("WEBHOOK_URL") or f"https://{os.getenv('VERCEL_PROJECT_PRODUCTION_URL')}{WEBHOOK_PATH}"
    await bot.set_webhook(url)
    logging.info("Webhook set: %s", url)
    yield
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    asyncio.create_task(dp.feed_update(bot, update))
    return {"ok": True}