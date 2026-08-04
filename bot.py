import asyncio
import io

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config

LIMIT = 5


def search_deezer(query: str) -> list:
    url = "https://api.deezer.com/search"
    params = {"q": query, "limit": LIMIT}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])


def search_itunes(query: str) -> list:
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "music", "entity": "song", "limit": LIMIT}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])


def track_info(r: dict) -> dict:
    return {
        "name": r.get("title") or r.get("trackName"),
        "artist": r.get("artist", {}).get("name") or r.get("artistName"),
        "album": r.get("album", {}).get("title") or r.get("collectionName"),
        "preview": r.get("preview") or r.get("previewUrl"),
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "\U0001F3B5 Qo'shiq nomini yozing, men topib beraman!\n"
        "Masalan: `Dua Lipa Levitating`\n\n"
        "Nomni topish uchun: sizga qo'shiqning 30 soniyalik snippet'i yuboriladi.",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text.strip()
    if len(query) < 2:
        return
    await update.message.chat.send_action("typing")
    results = await asyncio.to_thread(search_deezer, query)
    source = "Deezer"
    if not results:
        results = await asyncio.to_thread(search_itunes, query)
        source = "iTunes"
    if not results:
        await update.message.reply_text("Hech narsa topilmadi. Boshqa nom bilan urinib ko'ring.")
        return
    keyboard = []
    for i, r in enumerate(results):
        info = track_info(r)
        label = f"{info['artist']} \u2014 {info['name']}"
        if info["album"]:
            label += f" ({info['album']})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"play:{i}")])
    context.user_data["results"] = results
    await update.message.reply_text(
        f"Top natijalar ({source}):", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    i = int(query.data.split(":")[1])
    results = context.user_data.get("results", [])
    if not results or i >= len(results):
        await query.edit_message_text("Natija topilmadi, qayta qidiring.")
        return
    info = track_info(results[i])
    if not info["preview"]:
        await query.answer("Bu qo'shiq uchun preview mavjud emas", show_alert=True)
        return
    try:
        data = await asyncio.to_thread(
            lambda: requests.get(info["preview"], timeout=30).content
        )
        await query.message.reply_audio(
            io.BytesIO(data),
            title=info["name"],
            performer=info["artist"],
            filename=f"{info['artist']} - {info['name']}.mp3",
        )
    except Exception as e:
        await query.answer(f"Xatolik yuz berdi: {e}", show_alert=True)


def main() -> None:
    app = Application.builder().token(config.TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(play, pattern="^play:"))
    app.run_polling()


if __name__ == "__main__":
    main()
