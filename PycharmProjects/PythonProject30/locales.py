"""
Botning uch tildagi (O'zbek, Rus, Ingliz) matnlari
"""

WELCOME_TEXT = {
    "uz": "👋 Xush kelibsiz! Forex Signal Bot.\n\nIltimos, tilni tanlang:",
    "ru": "👋 Добро пожаловать! Forex Signal Bot.\n\nПожалуйста, выберите язык:",
    "en": "👋 Welcome! Forex Signal Bot.\n\nPlease choose your language:",
}

LANGUAGE_BUTTONS = [
    {"text": "🇺🇿 O'zbekcha", "callback_data": "lang_uz"},
    {"text": "🇷🇺 Русский", "callback_data": "lang_ru"},
    {"text": "🇬🇧 English", "callback_data": "lang_en"},
]

LANGUAGE_SET_TEXT = {
    "uz": "✅ Til O'zbekcha qilib o'rnatildi.\nBot endi {symbols} juftliklarini kuzatadi va sizga signal yuboradi.",
    "ru": "✅ Язык установлен: Русский.\nБот теперь отслеживает {symbols} и будет присылать вам сигналы.",
    "en": "✅ Language set to English.\nThe bot is now watching {symbols} and will send you signals.",
}

MARKET_CLOSED_TEXT = {
    "uz": (
        "📴 <b>Bozor hozir yopiq</b>\n\n"
        "Forex va oltin (XAU/USD) bozori shanba-yakshanba kunlari ishlamaydi.\n"
        "Bozor odatda <b>yakshanba kuni kechqurun (Sidney sessiyasi)</b> qayta ochiladi.\n\n"
        "Signal qidirish dam olish kunlarida to'xtatilgan. Bozor ochilishi bilan "
        "bot avtomatik qayta ishga tushadi."
    ),
    "ru": (
        "📴 <b>Рынок сейчас закрыт</b>\n\n"
        "Форекс и золото (XAU/USD) не торгуются по субботам и воскресеньям.\n"
        "Обычно рынок открывается <b>в воскресенье вечером (Сиднейская сессия)</b>.\n\n"
        "Поиск сигналов приостановлен на выходных. Бот автоматически возобновит "
        "работу при открытии рынка."
    ),
    "en": (
        "📴 <b>Market is currently closed</b>\n\n"
        "Forex and gold (XAU/USD) don't trade on Saturdays and Sundays.\n"
        "The market usually reopens <b>Sunday evening (Sydney session)</b>.\n\n"
        "Signal scanning is paused for the weekend. The bot will resume "
        "automatically once the market opens."
    ),
}

MARKET_OPEN_TEXT = {
    "uz": "✅ <b>Bozor hozir ochiq</b>\nBot faol ravishda signallarni kuzatmoqda.",
    "ru": "✅ <b>Рынок сейчас открыт</b>\nБот активно отслеживает сигналы.",
    "en": "✅ <b>Market is currently open</b>\nThe bot is actively scanning for signals.",
}

BOT_STARTED_BROADCAST = {
    "uz": (
        "🤖 <b>Forex Signal Bot ishga tushdi</b>\n"
        "Juftliklar: {symbols}\n"
        "Timeframe: {interval}\n"
        "Strategiya: SMA9/50 + RSI + MACD + EMA200 + ADX"
    ),
    "ru": (
        "🤖 <b>Forex Signal Bot запущен</b>\n"
        "Пары: {symbols}\n"
        "Таймфрейм: {interval}\n"
        "Стратегия: SMA9/50 + RSI + MACD + EMA200 + ADX"
    ),
    "en": (
        "🤖 <b>Forex Signal Bot started</b>\n"
        "Pairs: {symbols}\n"
        "Timeframe: {interval}\n"
        "Strategy: SMA9/50 + RSI + MACD + EMA200 + ADX"
    ),
}

SIGNAL_LABELS = {
    "uz": {
        "BUY": "SOTIB OLISH",
        "SELL": "SOTISH",
        "pair": "Juftlik",
        "entry": "Kirish narxi",
        "sl": "Stop-Loss",
        "tp": "Take-Profit",
        "rr": "Risk/Reward",
        "trend_strength": "Trend kuchi",
        "disclaimer": "⚠️ Bu avtomatik signal, moliyaviy maslahat emas. O'z tavakkalingizga tayaning va risk-menejmentni unutmang.",
    },
    "ru": {
        "BUY": "ПОКУПКА",
        "SELL": "ПРОДАЖА",
        "pair": "Пара",
        "entry": "Цена входа",
        "sl": "Стоп-лосс",
        "tp": "Тейк-профит",
        "rr": "Риск/Прибыль",
        "trend_strength": "Сила тренда",
        "disclaimer": "⚠️ Это автоматический сигнал, не является финансовым советом. Действуйте на свой риск и не забывайте про риск-менеджмент.",
    },
    "en": {
        "BUY": "BUY",
        "SELL": "SELL",
        "pair": "Pair",
        "entry": "Entry price",
        "sl": "Stop-Loss",
        "tp": "Take-Profit",
        "rr": "Risk/Reward",
        "trend_strength": "Trend strength",
        "disclaimer": "⚠️ This is an automated signal, not financial advice. Trade at your own risk and always use risk management.",
    },
}

DEFAULT_LANGUAGE = "uz"
