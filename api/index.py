import asyncio

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot import get_token, handle_message, play, start

app = FastAPI()

application: Application = None


def get_application() -> Application:
    global application
    if application is None:
        application = Application.builder().token(get_token()).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )
        application.add_handler(CallbackQueryHandler(play, pattern="^play:"))
    return application


@app.on_event("startup")
async def on_startup() -> None:
    await get_application().initialize()


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "music-search-bot"}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    data = await request.json()
    app = get_application()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return {"status": "ok"}


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if application is not None:
        await application.shutdown()
