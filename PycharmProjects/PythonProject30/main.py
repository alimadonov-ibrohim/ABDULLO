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
    PAIR_SELECTOR_TEXT, PAIR_ADDED_TEXT, PAIR_REMOVED_TEXT, PAIR_COMMAND_HINT_TEXT,
)
from user_store import (
    set_user_language, get_user_language, get_all_registered_chat_ids,
    get_all_users, get_user_symbols, toggle_user_symbol,
)


def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


def process_update(update: dict, notifier: TelegramNotifier):
    """Bitta Telegram update'ni qayta ishlaydi (polling va webhook uchun umumiy)."""
    # --- Oddiy matnli xabar (masalan /start yoki har qanday yozuv) ---
    message = update.get("message")
    if message:
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").strip()
        lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)

        if text == "/start":
            notifier.send_language_selector(chat_id, WELCOME_TEXT[lang])
        elif text in ("/pair", "/valyuta"):
            selected = get_user_symbols(chat_id, config.SYMBOLS)
            keyboard = notifier.build_pair_keyboard(config.AVAILABLE_SYMBOLS, selected)
            notifier.send_pair_selector(chat_id, PAIR_SELECTOR_TEXT[lang], keyboard)
        else:
            base = MARKET_CLOSED_TEXT[lang] if is_weekend() else MARKET_OPEN_TEXT[lang]
            notifier.send_message(base + "\n\n" + PAIR_COMMAND_HINT_TEXT[lang], chat_id=chat_id)

    # --- Til tanlash yoki juftlik tanlash tugmasi bosilganda ---
    callback = update.get("callback_query")
    if callback:
        chat_id = str(callback["message"]["chat"]["id"])
        data = callback.get("data", "")

        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_user_language(chat_id, lang)
            notifier.answer_callback_query(callback["id"])

            symbols_text = ", ".join(config.SYMBOLS)
            confirm_text = LANGUAGE_SET_TEXT[lang].format(symbols=symbols_text)
            confirm_text += "\n\n💱 " + PAIR_COMMAND_HINT_TEXT[lang]
            notifier.send_message(confirm_text, chat_id=chat_id)
            log(f"Foydalanuvchi {chat_id} tilni tanladi: {lang}")

        elif data.startswith("sym_"):
            symbol = data[len("sym_"):]
            lang = get_user_language(chat_id, default=DEFAULT_LANGUAGE)

            added = toggle_user_symbol(chat_id, symbol, config.SYMBOLS)
            feedback = (PAIR_ADDED_TEXT if added else PAIR_REMOVED_TEXT)[lang].format(symbol=symbol)
            notifier.answer_callback_query(callback["id"], text=feedback)

            selected = get_user_symbols(chat_id, config.SYMBOLS)
            keyboard = notifier.build_pair_keyboard(config.AVAILABLE_SYMBOLS, selected)
            notifier.edit_pair_keyboard(chat_id, callback["message"]["message_id"], keyboard)
            log(f"Foydalanuvchi {chat_id} juftlikni o'zgartirdi: {symbol} "
                f"({'qoshildi' if added else 'olindi'})")


def handle_updates(notifier: TelegramNotifier, offset: int):
    """Foydalanuvchidan kelgan xabar/tugma bosishlarni qayta ishlaydi. Yangi offset qaytaradi."""
    updates = notifier.get_updates(offset=offset, timeout=1)

    for update in updates:
        offset = update["update_id"] + 1
        process_update(update, notifier)

    return offset


def collect_targets() -> dict:
    """symbol -> [chat_id, ...] xaritasi: har kim qaysi juftliklarga obuna."""
    targets = {}
    for chat_id, info in get_all_users().items():
        syms = info.get("symbols") or config.SYMBOLS
        if isinstance(syms, str):
            syms = [syms]
        for s in syms:
            targets.setdefault(s, []).append(chat_id)
    return targets


def broadcast_signal(notifier: TelegramNotifier, symbol: str, signal: str, details: dict,
                     chat_ids: list):
    """Signalni berilgan foydalanuvchilarga, ularning o'z tilida yuboradi."""
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

    targets = collect_targets()
    symbols_to_check = list(targets.keys()) or list(config.SYMBOLS)
    fallback_recipients = [config.TELEGRAM_CHAT_ID] if config.TELEGRAM_CHAT_ID else []

    for symbol in symbols_to_check:
        try:
            df = fetcher.get_candles(symbol, interval=config.INTERVAL, outputsize=210)
            df = add_all_indicators(df)
            result = check_signal(df)

            last_candle_time = str(df.iloc[-1]["datetime"])

            if result["signal"] is not None:
                if last_signal_time.get(symbol) != last_candle_time:
                    recipients = targets.get(symbol) or fallback_recipients
                    if recipients:
                        broadcast_signal(notifier, symbol, result["signal"], result["details"], recipients)
                        log(f"{symbol}: {result['signal']} signali yuborildi "
                            f"({len(recipients)} kishiga).")
                    else:
                        log(f"{symbol}: {result['signal']} signal bor, lekin obunachi yo'q.")
                    last_signal_time[symbol] = last_candle_time
                    sent.append({"symbol": symbol, "signal": result["signal"],
                                 "recipients": len(recipients)})
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
