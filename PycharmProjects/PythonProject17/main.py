import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message
from dotenv import load_dotenv

from downloader import MAX_FILE_SIZE, SUPPORTED_RE, cleanup, download_video

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

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


async def main():
    logging.info("Bot ishga tushdi")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())