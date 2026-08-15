import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import ipakyuli_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "http://127.0.0.1:8000/webapp")

CURRENCIES = [("USD", "Dollar"), ("EUR", "Yevro"), ("RUB", "Rubl"), ("GBP", "Funt"), ("CHF", "Frank"), ("JPY", "Iyena")]
TABS = ["Kassada", "Bankomatda", "Ilovada"]
SIDES = [("buy", "Bank sotib oladi"), ("sell", "Bank sotadi")]

user_states = {}


def fmt(n):
    return f"{n:,}".replace(",", " ")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Kurslar", callback_data="kurs")],
        [InlineKeyboardButton("Hisoblagich", callback_data="hisob")],
        [InlineKeyboardButton("Web App (hisoblagich)", web_app=WebAppInfo(url=WEBAPP_URL))],
    ])
    await update.message.reply_text(
        "Salom! Ipak Yuli Bank valyuta kurslari boti.\n"
        "Tanlang: kurslarni ko'rish yoki valyuta hisoblash.",
        reply_markup=kb,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/kurs - joriy kurslar\n"
        "/hisob - valyuta hisoblagich\n"
        "Yoki bevosita: /hisob 100 USD buy\n"
        "/theme - qorong'u yoki oq mavzu (Web App uchun)"
    )


async def cmd_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌙 Qorong'u", callback_data="theme:dark")],
        [InlineKeyboardButton("☀️ Oq", callback_data="theme:light")],
    ])
    await update.message.reply_text("Web App uchun mavzuni tanlang:", reply_markup=kb)


async def cmd_kurs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = ipakyuli_api.get_rates()
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")
        return

    for tab in data["tabs"]:
        lines = [f"💱 {tab['name']}"]
        lines.append("Valyuta | Sotib oladi | Sotadi")
        lines.append("──" * 12)
        for r in tab["rates"]:
            lines.append(f"{r['code']} | {fmt(r['buy'])} | {fmt(r['sell'])}")
        await update.message.reply_text("\n".join(lines))

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Hisoblagich", callback_data="hisob")],
        [InlineKeyboardButton("Web App", web_app=WebAppInfo(url=WEBAPP_URL))],
    ])
    await update.message.reply_text("Hisoblashni xohlaysizmi?", reply_markup=kb)


async def cmd_hisob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) >= 3:
        try:
            amount = float(args[1].replace(",", "."))
            code = args[2].upper()
            side = args[3].lower() if len(args) > 3 else "buy"
            await show_result(update, amount, code, "Kassada", side)
            return
        except Exception:
            pass

    user_states[update.effective_user.id] = {"step": "amount", "tab": "Kassada", "side": "buy"}
    await update.message.reply_text(
        "Summani kiriting (masalan: 100 yoki 500.5), keyin valyutani tanlaysiz:"
    )


async def show_result(update, amount, code, tab, side):
    try:
        res = ipakyuli_api.convert(amount, code, tab, side)
        msg = (
            f"{fmt(res['amount'])} {res['from']} → {fmt(res['result'])} so'm\n"
            f"Kurs ({res['tab']}): {fmt(res['rate'])} so'm / 100 {res['from']}\n"
            f"Yo'nalish: {res['side']}"
        )
    except ValueError as e:
        msg = str(e)
    except Exception as e:
        msg = f"Xatolik: {e}"

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Yana hisoblash", callback_data="hisob")]])
    await update.message.reply_text(msg, reply_markup=kb)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_states.get(uid)
    if not state or state["step"] != "amount":
        await cmd_help(update, context)
        return

    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Iltimos, faqat son kiriting (masalan: 100).")
        return

    state["amount"] = amount
    state["step"] = "currency"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{c} — {n}", callback_data=f"cur:{c}") for c, n in CURRENCIES[:2]],
        [InlineKeyboardButton(f"{c} — {n}", callback_data=f"cur:{c}") for c, n in CURRENCIES[2:4]],
        [InlineKeyboardButton(f"{c} — {n}", callback_data=f"cur:{c}") for c, n in CURRENCIES[4:]],
    ])
    await update.message.reply_text(f"Summa: {amount}. Valyutani tanlang:", reply_markup=kb)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    data = query.data

    if data == "kurs":
        context.user_data.clear()
        user_states.pop(uid, None)
        await query.message.reply_text("Kurslar jadvali yuborilmoqda...")
        await cmd_kurs(update, context)
        return

    if data == "hisob":
        user_states[uid] = {"step": "amount", "tab": "Kassada", "side": "buy"}
        await query.message.reply_text("Summani kiriting (masalan: 100):")
        return

    if data.startswith("theme:"):
        theme = data.split(":", 1)[1]
        emoji = "🌙 Qorong'u" if theme == "dark" else "☀️ Oq"
        await query.message.reply_text(f"Tanlandi: {emoji}. Web App ochilganda qo'llanadi.")
        return

    if data.startswith("cur:"):
        code = data.split(":", 1)[1]
        state = user_states.get(uid, {})
        state["currency"] = code
        state["step"] = "side"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(s, callback_data=f"side:{v}") for v, s in SIDES],
        ])
        await query.message.reply_text(f"{code} tanlandi. Yo'nalishni tanlang:", reply_markup=kb)
        return

    if data.startswith("side:"):
        side = data.split(":", 1)[1]
        state = user_states.get(uid, {})
        if not state.get("amount") or not state.get("currency"):
            await query.message.reply_text("Boshidan boshlang: /hisob")
            return
        await show_result(
            update.effective_user,
            state["amount"],
            state["currency"],
            state.get("tab", "Kassada"),
            side,
        )
        user_states.pop(uid, None)
        return

    await query.message.reply_text("Noma'lum buyruq.")


def main():
    if not TOKEN:
        logger.error("BOT_TOKEN environment o'zgaruvchisi o'rnatilmagan!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("kurs", cmd_kurs))
    app.add_handler(CommandHandler("hisob", cmd_hisob))
    app.add_handler(CommandHandler("theme", cmd_theme))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()