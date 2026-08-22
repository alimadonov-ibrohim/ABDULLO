"""
FOREX SIGNAL BOT - asosiy ishga tushirish fayli
SMA9/50 kesishishi + RSI + MACD + EMA200 + ADX asosida signal beradi
/start bosilganda til tanlash (UZ/RU/EN) taklif qiladi

Ishga tushirish: python main.py
To'xtatish: Ctrl+C
"""
import time
from datetime import datetime

import config
from data_fetcher import DataFetcher
from indicators import add_all_indicators, check_signal
from telegram_notifier import TelegramNotifier
from market_hours import is_weekend
from locales import (
    WELCOME_TEXT, LANGUAGE_SET_TEXT, MARKET_CLOSED_TEXT, MARKET_OPEN_TEXT,
    BOT_STARTED_BROADCAST, DEFAULT_LANGUAGE,
)
from user_store import set_user_language, get_user_language, get_all_registered_chat_ids


def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


def process_update(update: dict, notifier: TelegramNotifier):
    """Bitta Telegram update'ni qayta ishlaydi (polling va webhook uchun umumiy)."""
    # --- Oddiy matnli xabar (masalan /start yoki har qanday yozuv) ---
    message = update.get("message")
    if message:
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")

        if text.strip() == "/start":
            lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)
            notifier.send_language_selector(chat_id, WELCOME_TEXT[lang])
        else:
            lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)
            status_text = MARKET_CLOSED_TEXT[lang] if is_weekend() else MARKET_OPEN_TEXT[lang]
            notifier.send_message(status_text, chat_id=chat_id)

    # --- Til tanlash tugmasi bosilganda ---
    callback = update.get("callback_query")
    if callback:
        chat_id = str(callback["message"]["chat"]["id"])
        data = callback.get("data", "")  # masalan "lang_uz"

        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_user_language(chat_id, lang)
            notifier.answer_callback_query(callback["id"])

            symbols_text = ", ".join(config.SYMBOLS)
            confirm_text = LANGUAGE_SET_TEXT[lang].format(symbols=symbols_text)
            notifier.send_message(confirm_text, chat_id=chat_id)
            log(f"Foydalanuvchi {chat_id} tilni tanladi: {lang}")


def handle_updates(notifier: TelegramNotifier, offset: int):
    """Foydalanuvchidan kelgan xabar/tugma bosishlarni qayta ishlaydi. Yangi offset qaytaradi."""
    updates = notifier.get_updates(offset=offset, timeout=1)

    for update in updates:
        offset = update["update_id"] + 1
        process_update(update, notifier)

    return offset


def broadcast_signal(notifier: TelegramNotifier, symbol: str, signal: str, details: dict):
    """Signalni tilni tanlagan barcha foydalanuvchilarga, ularning o'z tilida yuboradi."""
    chat_ids = get_all_registered_chat_ids()
    if not chat_ids and config.TELEGRAM_CHAT_ID:
        # Hech kim /start bosmagan bo'lsa, config'dagi standart chat_id'ga yuboriladi
        chat_ids = [config.TELEGRAM_CHAT_ID]

    for chat_id in chat_ids:
        lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)
        text = notifier.format_signal_message(symbol, signal, details, lang=lang)
        notifier.send_message(text, chat_id=chat_id)


def broadcast_weekend_notice(notifier: TelegramNotifier):
    chat_ids = get_all_registered_chat_ids()
    if not chat_ids and config.TELEGRAM_CHAT_ID:
        chat_ids = [config.TELEGRAM_CHAT_ID]
    for chat_id in chat_ids:
        lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)
        notifier.send_message(MARKET_CLOSED_TEXT[lang], chat_id=chat_id)


def run_check_cycle(fetcher: DataFetcher, notifier: TelegramNotifier, last_signal_time: dict,
                    ignore_weekend: bool = False) -> list:
    """Bitta kuzatuv tsikli: barcha juftliklar uchun signal tekshiradi.
    Yuborilgan signallar ro'yxatini qaytaradi (serverless cron uchun ham ishlatiladi)."""
    sent = []
    if is_weekend() and not ignore_weekend:
        log("Bugun dam olish kuni. Bozor yopiq.")
        return sent

    for symbol in config.SYMBOLS:
        try:
            df = fetcher.get_candles(symbol, interval=config.INTERVAL, outputsize=210)
            df = add_all_indicators(df)
            result = check_signal(df)

            last_candle_time = str(df.iloc[-1]["datetime"])

            if result["signal"] is not None:
                if last_signal_time.get(symbol) != last_candle_time:
                    broadcast_signal(notifier, symbol, result["signal"], result["details"])
                    last_signal_time[symbol] = last_candle_time
                    log(f"{symbol}: {result['signal']} signali yuborildi.")
                    sent.append({"symbol": symbol, "signal": result["signal"]})
                else:
                    log(f"{symbol}: signal bor, lekin allaqachon yuborilgan.")
            else:
                log(f"{symbol}: signal yo'q. RSI={result['details'].get('rsi')}, "
                    f"ADX={result['details'].get('adx')}")

        except Exception as e:
            log(f"{symbol}: XATOLIK - {e}")

    return sent


def main():
    fetcher = DataFetcher(config.TWELVE_DATA_API_KEY)
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    last_signal_time = {symbol: None for symbol in config.SYMBOLS}
    update_offset = None
    weekend_notice_sent = False

    log("Bot ishga tushdi. Kuzatilayotgan juftliklar: " + ", ".join(config.SYMBOLS))

    symbols_text = ", ".join(config.SYMBOLS)
    for chat_id in (get_all_registered_chat_ids() or [config.TELEGRAM_CHAT_ID]):
        if not chat_id:
            continue
        lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)
        notifier.send_message(
            BOT_STARTED_BROADCAST[lang].format(symbols=symbols_text, interval=config.INTERVAL),
            chat_id=chat_id,
        )

    while True:
        # --- Foydalanuvchi xabarlarini/tugmalarini qayta ishlash ---
        update_offset = handle_updates(notifier, update_offset)

        # --- Dam olish kuni tekshiruvi ---
        if is_weekend():
            if not weekend_notice_sent:
                log("Bugun dam olish kuni. Bozor yopiq, signal qidirish to'xtatildi.")
                broadcast_weekend_notice(notifier)
                weekend_notice_sent = True
            time.sleep(config.CHECK_INTERVAL_SECONDS)
            continue
        else:
            weekend_notice_sent = False

        run_check_cycle(fetcher, notifier, last_signal_time)

        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
