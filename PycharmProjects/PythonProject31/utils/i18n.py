"""Uch tilli matnlar: uz / ru / en."""

CREATOR_NAME = "ALIMARDONOV IBROHIM"

DEFAULT_LANG = "uz"
SUPPORTED_LANGS: dict[str, str] = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

_lang_cache: dict[int, str] = {}

TEXTS: dict[str, dict[str, str]] = {
    # ---------- umumiy / menyu ----------
    "choose_lang": {
        "uz": "🌐 <b>Tilni tanlang:</b>",
        "ru": "🌐 <b>Выберите язык:</b>",
        "en": "🌐 <b>Choose a language:</b>",
    },
    "welcome": {
        "uz": "👋 Salom, <b>{name}</b>!\n\n🤖 Men Forex va kripto bozorlarini 24/7 kuzatib boraman.",
        "ru": "👋 Привет, <b>{name}</b>!\n\n🤖 Я круглосуточно слежу за рынками Forex и крипты.",
        "en": "👋 Hi, <b>{name}</b>!\n\n🤖 I monitor Forex and crypto markets 24/7.",
    },
    "welcome_stats": {
        "uz": "📊 <b>{pairs}</b> juftlik · ⏱ M15–D1 · 8+ indikator\n⚡️ Bugunga qadar <b>{n}</b> ta signal generatsiya qildim",
        "ru": "📊 <b>{pairs}</b> пар · ⏱ M15–D1 · 8+ индикаторов\n⚡️ На данный момент выдано <b>{n}</b> сигналов",
        "en": "📊 <b>{pairs}</b> pairs · ⏱ M15–D1 · 8+ indicators\n⚡️ Generated <b>{n}</b> signals so far",
    },
    "welcome_vip_line": {
        "uz": "💎 VIP a'zolik: <b>faol</b> ({until} gacha)",
        "ru": "💎 VIP-статус: <b>активен</b> (до {until})",
        "en": "💎 VIP membership: <b>active</b> (until {until})",
    },
    "welcome_cta": {
        "uz": "👇 Boshlash uchun <b>«📊 Tahlil»</b> tugmasini bosing yoki juftlik nomini yozing",
        "ru": "👇 Нажмите <b>«📊 Анализ»</b> или напишите название пары",
        "en": "👇 Press <b>“📊 Analyze”</b> or just type a pair name",
    },
    "btn_analysis": {
        "uz": "📊 Tahlil qilish",
        "ru": "📊 Анализировать",
        "en": "📊 Analyze",
    },
    "btn_vip": {"uz": "💎 VIP", "ru": "💎 VIP", "en": "💎 VIP"},
    "btn_vip_priced": {
        "uz": "💎 VIP · ${price}/oydan",
        "ru": "💎 VIP · от ${price}/мес",
        "en": "💎 VIP · from ${price}/mo",
    },
    "btn_history": {"uz": "📜 Tarix", "ru": "📜 История", "en": "📜 History"},
    "btn_stats": {"uz": "📈 Statistika", "ru": "📈 Статистика", "en": "📈 Statistics"},
    "btn_help": {"uz": "ℹ️ Yordam", "ru": "ℹ️ Помощь", "en": "ℹ️ Help"},
    "btn_info": {
        "uz": "📚 Ma'lumotlar",
        "ru": "📚 Информация",
        "en": "📚 About",
    },
    "btn_clear": {
        "uz": "🧹 Chatni tozalash",
        "ru": "🧹 Очистить чат",
        "en": "🧹 Clear chat",
    },
    "btn_pairs_list": {
        "uz": "📊 Juftlik tahlili",
        "ru": "📊 Анализ пары",
        "en": "📊 Pair analysis",
    },
    "btn_vip_sub": {
        "uz": "💎 VIP obuna",
        "ru": "💎 VIP подписка",
        "en": "💎 VIP subscription",
    },
    "btn_signal_history": {
        "uz": "📜 Signal tarixi",
        "ru": "📜 История сигналов",
        "en": "📜 Signal history",
    },
    "btn_back_main": {
        "uz": "🔙 Asosiy menyu",
        "ru": "🔙 Главное меню",
        "en": "🔙 Main menu",
    },
    "btn_refresh": {"uz": "🔄 Yangilash", "ru": "🔄 Обновить", "en": "🔄 Refresh"},
    "btn_custom_pair": {
        "uz": "✍️ Boshqa juftlik (yozing)",
        "ru": "✍️ Другая пара (введите)",
        "en": "✍️ Other pair (type it)",
    },
    # ---------- yordam ----------
    "help_text": {
        "uz": (
            "ℹ️ <b>Yordam</b>\n\n"
            "<b>Buyruqlar:</b>\n"
            "/start — botni ishga tushirish\n"
            "/menu — asosiy menyu\n"
            "/vip — VIP obuna haqida\n"
            "/stats — statistika\n"
            "/clear — chatni tozalash (kamdan-kam kerak)\n"
            "/creator — yaratuvchi haqida\n\n"
            "<b>Tahlil qanday ishlaydi?</b>\n"
            "1️⃣ Juftlikni tanlaysiz (yoki o'zingiz yozasiz)\n"
            "2️⃣ Bot M15/H1/H4/D1 da 8+ indikatorni hisoblaydi\n"
            "3️⃣ Sham naqshlari va narx figuralarini skanerlaydi\n"
            "4️⃣ Og'irlikli ball (−100…+100) bo'yicha yo'nalish aniqlanadi\n"
            "5️⃣ Entry, SL, TP1-TP3 va Risk/Reward rejasi beriladi\n\n"
            "🗓 <b>Ish vaqti:</b> bozor dushanba–juma kunlari ochiq "
            "(shanba/yakshanba dam oladi).\n\n"
            "⚠️ <i>Signallar moliyaviy maslahat emas. Risklarni boshqaring!</i>"
        ),
        "ru": (
            "ℹ️ <b>Помощь</b>\n\n"
            "<b>Команды:</b>\n"
            "/start — запустить бота\n"
            "/menu — главное меню\n"
            "/vip — о VIP подписке\n"
            "/stats — статистика\n"
            "/clear — очистить чат (редко нужно)\n"
            "/creator — о создателе\n\n"
            "<b>Как работает анализ?</b>\n"
            "1️⃣ Выбираете пару (или вводите сами)\n"
            "2️⃣ Бот считает 8+ индикаторов на M15/H1/H4/D1\n"
            "3️⃣ Сканирует свечные паттерны и фигуры\n"
            "4️⃣ Направление определяется по взвешенному баллу (−100…+100)\n"
            "5️⃣ Даёт вход, SL, TP1-TP3 и план Risk/Reward\n\n"
            "🗓 <b>Время работы:</b> рынок открыт пн–пт "
            "(сб/вс — выходной).\n\n"
            "⚠️ <i>Сигналы не являются финансовой рекомендацией. Управляйте рисками!</i>"
        ),
        "en": (
            "ℹ️ <b>Help</b>\n\n"
            "<b>Commands:</b>\n"
            "/start — start the bot\n"
            "/menu — main menu\n"
            "/vip — about VIP subscription\n"
            "/stats — statistics\n"
            "/clear — clear the chat (rarely needed)\n"
            "/creator — about the creator\n\n"
            "<b>How does the analysis work?</b>\n"
            "1️⃣ Pick a pair (or type your own)\n"
            "2️⃣ The bot calculates 8+ indicators on M15/H1/H4/D1\n"
            "3️⃣ Scans candle patterns and chart figures\n"
            "4️⃣ Detects direction via weighted score (−100…+100)\n"
            "5️⃣ Provides entry, SL, TP1-TP3 and Risk/Reward plan\n\n"
            "🗓 <b>Working hours:</b> market open Mon–Fri "
            "(closed Sat/Sun).\n\n"
            "⚠️ <i>Signals are not financial advice. Manage your risks!</i>"
        ),
    },
    # ---------- ma'lumotlar ----------
    "info_text": {
        "uz": (
            "📚 <b>Bot ma'lumotlari</b>\n\n"
            "⚡️ <b>Imkoniyatlarim:</b>\n"
            "• 📊 RSI, MACD, Stochastic, Bollinger, EMA 50/200, Ichimoku, ADX\n"
            "• ⏱ M15 / H1 / H4 / D1 ko'p timeframe tahlili (og'irlikli ball)\n"
            "• 🕯 Sham naqshlari va narx figuralari\n"
            "• 🧭 Market struktura (BOS/CHoCH) va likvidlik zonalari\n"
            "• 🎯 Entry, TP1-TP3, SL va Risk/Reward\n\n"
            f"👨‍💻 Yaratuvchi: <b>{CREATOR_NAME}</b>"
        ),
        "ru": (
            "📚 <b>Информация о боте</b>\n\n"
            "⚡️ <b>Возможности:</b>\n"
            "• 📊 RSI, MACD, Stochastic, Bollinger, EMA 50/200, Ichimoku, ADX\n"
            "• ⏱ Анализ M15 / H1 / H4 / D1 (взвешенный балл)\n"
            "• 🕯 Свечные паттерны и фигуры цены\n"
            "• 🧭 Структура рынка (BOS/CHoCH) и зоны ликвидности\n"
            "• 🎯 Вход, TP1-TP3, SL и Risk/Reward\n\n"
            f"👨‍💻 Создатель: <b>{CREATOR_NAME}</b>"
        ),
        "en": (
            "📚 <b>Bot information</b>\n\n"
            "⚡️ <b>Features:</b>\n"
            "• 📊 RSI, MACD, Stochastic, Bollinger, EMA 50/200, Ichimoku, ADX\n"
            "• ⏱ M15 / H1 / H4 / D1 multi-timeframe analysis (weighted score)\n"
            "• 🕯 Candlestick patterns & chart figures\n"
            "• 🧭 Market structure (BOS/CHoCH) and liquidity zones\n"
            "• 🎯 Entry, TP1-TP3, SL and Risk/Reward\n\n"
            f"👨‍💻 Creator: <b>{CREATOR_NAME}</b>"
        ),
    },
    "clear_done": {
        "uz": "🧹 Chat tozalandi.",
        "ru": "🧹 Чат очищен.",
        "en": "🧹 Chat cleared.",
    },
    # ---------- statistika ----------
    "stats_title": {
        "uz": "📈 <b>Umumiy statistika</b>",
        "ru": "📈 <b>Общая статистика</b>",
        "en": "📈 <b>Overall statistics</b>",
    },
    "stats_users": {
        "uz": "👥 Foydalanuvchilar: <b>{n}</b>",
        "ru": "👥 Пользователи: <b>{n}</b>",
        "en": "👥 Users: <b>{n}</b>",
    },
    "stats_today": {
        "uz": "📡 Bugungi signallar: <b>{n}</b>",
        "ru": "📡 Сигналы за сегодня: <b>{n}</b>",
        "en": "📡 Today's signals: <b>{n}</b>",
    },
    "stats_total": {
        "uz": "📊 <b>Jami signallar:</b> <b>{n}</b>",
        "ru": "📊 <b>Всего сигналов:</b> <b>{n}</b>",
        "en": "📊 <b>Total signals:</b> <b>{n}</b>",
    },
    "stats_long_short": {
        "uz": "• 🟢 LONG: {long} · 🔴 SHORT: {short}",
        "ru": "• 🟢 LONG: {long} · 🔴 SHORT: {short}",
        "en": "• 🟢 LONG: {long} · 🔴 SHORT: {short}",
    },
    "stats_long_share": {
        "uz": "[{bar}] Long ulushi {pct}%",
        "ru": "[{bar}] Доля Long {pct}%",
        "en": "[{bar}] Long share {pct}%",
    },
    "stats_top": {
        "uz": "\n🏆 <b>Top juftliklar:</b>",
        "ru": "\n🏆 <b>Топ пары:</b>",
        "en": "\n🏆 <b>Top pairs:</b>",
    },
    "stats_avg_conf": {
        "uz": "\n🎯 O'rtacha ishonch darajasi: <b>{pct}%</b>",
        "ru": "\n🎯 Средняя уверенность: <b>{pct}%</b>",
        "en": "\n🎯 Average confidence: <b>{pct}%</b>",
    },
    # ---------- sinov (trial) rejimi ----------
    "tv_unavailable": {
        "uz": (
            "⏳ <b>Ma'lumot vaqtincha olinmadi</b>\n\n"
            "Bozor ma'lumotlari manbasi hozir javob bermayapti "
            "(bandlik yoki texnik tanaffus).\n"
            "💡 Bir-ikki daqiqadan keyin qayta urinib ko'ring."
        ),
        "ru": (
            "⏳ <b>Данные временно недоступны</b>\n\n"
            "Источник рыночных данных сейчас не отвечает "
            "(нагрузка или технический перерыв).\n"
            "💡 Попробуйте снова через минуту-две."
        ),
        "en": (
            "⏳ <b>Data temporarily unavailable</b>\n\n"
            "The market data source is not responding right now "
            "(high load or maintenance).\n"
            "💡 Please try again in a minute or two."
        ),
    },
    "welcome_trial_line": {
        "uz": "🎁 <b>Sinov rejimi faol!</b> Kuniga {n} ta bepul signal · {left} kun qoldi",
        "ru": "🎁 <b>Пробный режим активен!</b> {n} бесплатных сигналов в день · осталось {left} дн.",
        "en": "🎁 <b>Trial active!</b> {n} free signals per day · {left} days left",
    },
    "trial_limit_reached": {
        "uz": (
            "⛔️ <b>Bugungi bepul limit tugadi!</b>\n\n"
            "Sinov rejimida kuniga {n} ta signal beriladi.\n"
            "💎 Cheksiz signallar va barcha imkoniyatlar uchun VIP oling: /vip"
        ),
        "ru": (
            "⛔️ <b>Дневной бесплатный лимит исчерпан!</b>\n\n"
            "В пробном режиме — {n} сигнала в день.\n"
            "💎 Безлимитные сигналы — с VIP: /vip"
        ),
        "en": (
            "⛔️ <b>Daily free limit reached!</b>\n\n"
            "Trial mode gives {n} signals per day.\n"
            "💎 Get unlimited signals with VIP: /vip"
        ),
    },
    # ---------- to'lov / premium ----------
    "pay_choose_method": {
        "uz": "💳 <b>To'lov usulini tanlang:</b>",
        "ru": "💳 <b>Выберите способ оплаты:</b>",
        "en": "💳 <b>Choose a payment method:</b>",
    },
    "pay_stars_btn": {
        "uz": "⭐️ Telegram Stars (avtomatik)",
        "ru": "⭐️ Telegram Stars (автоматически)",
        "en": "⭐️ Telegram Stars (instant)",
    },
    "pay_manual_btn": {
        "uz": "👨‍💼 Admin orqali (karta/kripto)",
        "ru": "👨‍💼 Через админа (карта/крипто)",
        "en": "👨‍💼 Via admin (card/crypto)",
    },
    "pay_invoice_desc": {
        "uz": "TradePulseAI VIP — {desc}",
        "ru": "TradePulseAI VIP — {desc}",
        "en": "TradePulseAI VIP — {desc}",
    },
    "pay_manual_title": {
        "uz": (
            "👨‍💼 <b>Admin orqali to'lash — {label} (${price})</b>\n\n"
            "1. Quyidagi karta yoki hamyonga to'lov qiling\n"
            "2. Chek/rasmni adminga yuboring\n"
            "3. Admin tasdiqlagach VIP avtomatik faollashadi"
        ),
        "ru": (
            "👨‍💼 <b>Оплата через админа — {label} (${price})</b>\n\n"
            "1. Оплатите на карту или кошелёк ниже\n"
            "2. Отправьте чек админу\n"
            "3. После подтверждения VIP активируется"
        ),
        "en": (
            "👨‍💼 <b>Pay via admin — {label} (${price})</b>\n\n"
            "1. Send payment to the card/wallet below\n"
            "2. Send the receipt to the admin\n"
            "3. VIP activates after approval"
        ),
    },
    "pay_manual_contact": {
        "uz": "👨‍💼 Admin: {contact}",
        "ru": "👨‍💼 Админ: {contact}",
        "en": "👨‍💼 Admin: {contact}",
    },
    "pay_i_paid_btn": {
        "uz": "✅ To'lov qildim",
        "ru": "✅ Я оплатил",
        "en": "✅ I have paid",
    },
    "pay_send_receipt": {
        "uz": (
            "🧾 Buyurtmangiz qabul qilindi!\n\n"
            "<b>Endi chek/rasmni shu chatga yuboring</b> — "
            "admin tez orada tekshirib, VIP'ni faollashtiradi.\n"
            "💡 Shoshilinch bo'lsa, admin bilan bog'laning."
        ),
        "ru": (
            "🧾 Заказ принят!\n\n"
            "<b>Теперь отправьте чек/скриншот в этот чат</b> — "
            "админ скоро проверит и активирует VIP.\n"
            "💡 Срочно? Свяжитесь с админом."
        ),
        "en": (
            "🧾 Order received!\n\n"
            "<b>Now send your receipt/screenshot to this chat</b> — "
            "the admin will review and activate your VIP shortly.\n"
            "💡 In a hurry? Contact the admin."
        ),
    },
    "pay_receipt_thanks": {
        "uz": (
            "✅ Chekingiz adminga yuborildi!\n"
            "Tasdiqlangach VIP avtomatik faollashadi."
        ),
        "ru": (
            "✅ Чек отправлен админу!\n"
            "После подтверждения VIP активируется автоматически."
        ),
        "en": (
            "✅ Your receipt was sent to the admin!\n"
            "VIP activates automatically after approval."
        ),
    },
    "pay_already_pending": {
        "uz": "⏳ Bu reja bo'yicha buyurtmangiz allaqachon kutilmoqda.",
        "ru": "⏳ Заказ по этому плану уже на рассмотрении.",
        "en": "⏳ An order for this plan is already pending.",
    },
    "pay_thanks_stars": {
        "uz": "🎉 To'lov uchun rahmat! VIP obuna faollashtirildi.",
        "ru": "🎉 Спасибо за оплату! VIP-подписка активирована.",
        "en": "🎉 Thanks for your payment! VIP subscription activated.",
    },
    "pay_failed": {
        "uz": "❌ To'lovni boshlab bo'lmadi. Keyinroq urinib ko'ring.",
        "ru": "❌ Не удалось начать оплату. Попробуйте позже.",
        "en": "❌ Failed to start payment. Please try again later.",
    },
    "pay_rejected": {
        "uz": (
            "❌ Sizning to'lov buyurtmangiz bekor qilindi.\n"
            "Savollar uchun admin bilan bog'laning."
        ),
        "ru": (
            "❌ Ваш заказ отклонён.\n"
            "По вопросам свяжитесь с админом."
        ),
        "en": (
            "❌ Your payment order was rejected.\n"
            "Contact the admin if you have questions."
        ),
    },
    "vip_activated": {
        "uz": (
            "💎 Tabriklaymiz! <b>{label}</b> faollashtirildi!\n"
            "📅 Amal qilish muddati: <b>{until}</b> UTC\n"
            "⚡️ Endi avto-signallarni birinchi bo'lib olasiz!"
        ),
        "ru": (
            "💎 Поздравляем! <b>{label}</b> активирован!\n"
            "📅 Действует до: <b>{until}</b> UTC\n"
            "⚡️ Теперь вы первым получаете авто-сигналы!"
        ),
        "en": (
            "💎 Congrats! <b>{label}</b> activated!\n"
            "📅 Valid until: <b>{until}</b> UTC\n"
            "⚡️ You now receive auto signals first!"
        ),
    },
    # ---------- signal kuzatuvi / winrate ----------
    "stats_winrate_title": {
        "uz": "📊 <b>Real natijalar (avto-signallar):</b>",
        "ru": "📊 <b>Реальные результаты (авто-сигналы):</b>",
        "en": "📊 <b>Real results (auto signals):</b>",
    },
    "stats_winrate_line": {
        "uz": (
            "✅ Winrate: <b>{pct}%</b> — {won} g'alaba · {lost} zarar\n"
            "📈 G'alabalarda o'rtacha TP darajasi: {avg_tp}"
        ),
        "ru": (
            "✅ Винрейт: <b>{pct}%</b> — {won} побед · {lost} убытков\n"
            "📈 Средний уровень TP в победах: {avg_tp}"
        ),
        "en": (
            "✅ Winrate: <b>{pct}%</b> — {won} wins · {lost} losses\n"
            "📈 Average TP level in wins: {avg_tp}"
        ),
    },
    "stats_winrate_none": {
        "uz": "<i>Kuzatuv yangi boshlandi — yopilgan signal hali yo'q.</i>",
        "ru": "<i>Отслеживание только началось — закрытых сигналов пока нет.</i>",
        "en": "<i>Tracking just started — no closed signals yet.</i>",
    },
    "stats_running": {
        "uz": "⏳ Kuzatilmoqda: {n} ta signal (TP1/TP2 urilgan)",
        "ru": "⏳ Отслеживаются: {n} сигн. (TP1/TP2 достигнуты)",
        "en": "⏳ In tracking: {n} signals (TP1/TP2 hit)",
    },
    # ---------- bozor vaqti ----------
    "market_closed": {
        "uz": (
            "🔴 <b>Bugun bozor yopiq!</b>\n\n"
            "🗓 Shanba va yakshanba — dam olish kunlari.\n"
            "Bozor <b>dushanba</b> kuni ochiladi.\n\n"
            "💡 Dushanba kuni qaytib kelib, tahlil so'rashingiz mumkin."
        ),
        "ru": (
            "🔴 <b>Сегодня рынок закрыт!</b>\n\n"
            "🗓 Суббота и воскресенье — выходные дни.\n"
            "Рынок откроется в <b>понедельник</b>.\n\n"
            "💡 Возвращайтесь в понедельник за анализом."
        ),
        "en": (
            "🔴 <b>The market is closed today!</b>\n\n"
            "🗓 Saturday and Sunday are days off.\n"
            "The market opens on <b>Monday</b>.\n\n"
            "💡 Come back on Monday for an analysis."
        ),
    },
    "weekend_note": {
        "uz": "\n⚠️ <i>Bugun shanba/yakshanba — bozor yopiq. Tahlil dushanbadan jumagacha.</i>",
        "ru": "\n⚠️ <i>Сегодня сб/вс — рынок закрыт. Анализ с понедельника по пятницу.</i>",
        "en": "\n⚠️ <i>Today is Sat/Sun — market closed. Analysis Mon–Fri only.</i>",
    },
    # ---------- blok ----------
    "banned_msg": {
        "uz": "🚫 <b>Siz botdan bloklangansiz.</b>\nAdmin bilan bog'laning.",
        "ru": "🚫 <b>Вы заблокированы в боте.</b>\nСвяжитесь с администратором.",
        "en": "🚫 <b>You are blocked from this bot.</b>\nContact the administrator.",
    },
    "ban_notify": {
        "uz": "🚫 Siz botdan bloklandingiz. Xizmatlar mavjud emas.",
        "ru": "🚫 Вы заблокированы. Сервисы недоступны.",
        "en": "🚫 You have been blocked. Services unavailable.",
    },
    "unban_notify": {
        "uz": "✅ Siz blokdan chiqarildingiz! Bot qayta ishlayapti.",
        "ru": "✅ Вы разблокированы! Бот снова доступен.",
        "en": "✅ You have been unblocked! The bot works again.",
    },
    # ---------- yaratuvchi ----------
    "creator_text": {
        "uz": (
            "👑 <b>Bot yaratuvchisi</b>\n\n"
            f"👨‍💻 <b>{CREATOR_NAME}</b>\n\n"
            "💎 Professional Forex & Crypto Analytics Bot\n"
            "📅 2026"
        ),
        "ru": (
            "👑 <b>Создатель бота</b>\n\n"
            f"👨‍💻 <b>{CREATOR_NAME}</b>\n\n"
            "💎 Professional Forex & Crypto Analytics Bot\n"
            "📅 2026"
        ),
        "en": (
            "👑 <b>Bot creator</b>\n\n"
            f"👨‍💻 <b>{CREATOR_NAME}</b>\n\n"
            "💎 Professional Forex & Crypto Analytics Bot\n"
            "📅 2026"
        ),
    },
    # ---------- tahlil ----------
    "pairs_menu_text": {
        "uz": (
            "📊 <b>Juftlikni tanlang</b>\n\n"
            "Kripto va Forex juftliklari mavjud. Ro'yxatda yo'q bo'lsa — "
            "✍️ qo'lda yozing (masalan: <code>TONUSDT</code>).{note}"
        ),
        "ru": (
            "📊 <b>Выберите пару</b>\n\n"
            "Доступны крипто и форекс пары. Нет в списке — ✍️ введите вручную "
            "(например: <code>TONUSDT</code>).{note}"
        ),
        "en": (
            "📊 <b>Pick a pair</b>\n\n"
            "Crypto and forex pairs available. Not in the list — ✍️ type it "
            "(e.g. <code>TONUSDT</code>).{note}"
        ),
    },
    "history_title": {
        "uz": "📜 <b>Oxirgi 10 signal:</b>\n",
        "ru": "📜 <b>Последние 10 сигналов:</b>\n",
        "en": "📜 <b>Last 10 signals:</b>\n",
    },
    "history_empty": {
        "uz": "📜 Hozircha signallar tarixi bo'sh.",
        "ru": "📜 История сигналов пока пуста.",
        "en": "📜 Signal history is empty so far.",
    },
    "analyzing_cb": {
        "uz": "⏳ Tahlilanmoqda...",
        "ru": "⏳ Анализируется...",
        "en": "⏳ Analyzing...",
    },
    "refreshing_cb": {
        "uz": "🔄 Yangilanyapti...",
        "ru": "🔄 Обновляется...",
        "en": "🔄 Refreshing...",
    },
    "analyzing_placeholder": {
        "uz": (
            "⏳ <b>{sym}</b> bo'yicha MTF tahlil hisoblanmoqda...\n"
            "<i>(TradingView, RSI, MACD, Ichimoku, ADX, naqshlar...)</i>"
        ),
        "ru": (
            "⏳ Считается MTF-анализ по <b>{sym}</b>...\n"
            "<i>(TradingView, RSI, MACD, Ichimoku, ADX, паттерны...)</i>"
        ),
        "en": (
            "⏳ Calculating MTF analysis for <b>{sym}</b>...\n"
            "<i>(TradingView, RSI, MACD, Ichimoku, ADX, patterns...)</i>"
        ),
    },
    "analysis_failed": {
        "uz": (
            "❌ <b>{sym}</b> tahlili bajarilmadi.\n"
            "Belgini tekshiring (masalan <code>BTCUSDT</code>, <code>EURUSD</code>) "
            "yoki keyinroq qayta urinib ko'ring."
        ),
        "ru": (
            "❌ Не удалось проанализировать <b>{sym}</b>.\n"
            "Проверьте тикер (<code>BTCUSDT</code>, <code>EURUSD</code>) "
            "или попробуйте позже."
        ),
        "en": (
            "❌ Failed to analyze <b>{sym}</b>.\n"
            "Check the ticker (e.g. <code>BTCUSDT</code>, <code>EURUSD</code>) "
            "or try again later."
        ),
    },
    "analyzing_simple": {
        "uz": "⏳ <b>{sym}</b> tahlilanmoqda...",
        "ru": "⏳ Анализируется <b>{sym}</b>...",
        "en": "⏳ Analyzing <b>{sym}</b>...",
    },
    "invalid_symbol": {
        "uz": "❌ Noto'g'ri format. Masalan: <code>BTCUSDT</code> yoki <code>EURUSD</code>",
        "ru": "❌ Неверный формат. Например: <code>BTCUSDT</code> или <code>EURUSD</code>",
        "en": "❌ Invalid format. Example: <code>BTCUSDT</code> or <code>EURUSD</code>",
    },
    "custom_prompt": {
        "uz": (
            "✍️ Juftlik belgisini yozing:\n\n"
            "• Kripto: <code>BTCUSDT</code>, <code>SOLUSDT</code>\n"
            "• Forex: <code>EURUSD</code>, <code>XAUUSD</code>"
        ),
        "ru": (
            "✍️ Введите тикер пары:\n\n"
            "• Крипто: <code>BTCUSDT</code>, <code>SOLUSDT</code>\n"
            "• Форекс: <code>EURUSD</code>, <code>XAUUSD</code>"
        ),
        "en": (
            "✍️ Type the pair ticker:\n\n"
            "• Crypto: <code>BTCUSDT</code>, <code>SOLUSDT</code>\n"
            "• Forex: <code>EURUSD</code>, <code>XAUUSD</code>"
        ),
    },
    # ---------- fallback ----------
    "fallback_unknown_cmd": {
        "uz": "❓ Noma'lum buyruq. /start ni bosing.",
        "ru": "❓ Неизвестная команда. Нажмите /start.",
        "en": "❓ Unknown command. Press /start.",
    },
    "fallback_text": {
        "uz": "🤖 Buyruqlar uchun /start yoki /menu dan foydalaning.\nJuftlik tahlili uchun 📊 Tahlil tugmasini bosing.",
        "ru": "🤖 Используйте /start или /menu для команд.\nДля анализа пары нажмите кнопку 📊 Анализ.",
        "en": "🤖 Use /start or /menu for commands.\nPress the 📊 Analysis button to analyze a pair.",
    },
    "unknown_callback_alert": {
        "uz": "⚠️ Tugma eskirgan. /start ni bosib menyuni yangilang.",
        "ru": "⚠️ Кнопка устарела. Нажмите /start и обновите меню.",
        "en": "⚠️ Button expired. Press /start to refresh the menu.",
    },
    # ---------- VIP ----------
    "vip_title": {
        "uz": "💎 <b>VIP OBUNA</b>",
        "ru": "💎 <b>VIP ПОДПИСКА</b>",
        "en": "💎 <b>VIP SUBSCRIPTION</b>",
    },
    "vip_active": {
        "uz": "✅ <b>Siz VIP a'zosiz!</b>\n📅 Amal qilish muddati: <b>{until}</b>\n\n⚡️ Avto-signal kanali: <b>faol</b>",
        "ru": "✅ <b>Вы VIP-участник!</b>\n📅 Действует до: <b>{until}</b>\n\n⚡️ Канал авто-сигналов: <b>активен</b>",
        "en": "✅ <b>You are a VIP member!</b>\n📅 Valid until: <b>{until}</b>\n\n⚡️ Auto-signal channel: <b>active</b>",
    },
    "vip_not_active": {
        "uz": "❌ Siz hozircha <b>oddiy foydalanuvchisiz</b>.\nRejalardan birini tanlab, admin bilan bog'laning.",
        "ru": "❌ Сейчас вы <b>обычный пользователь</b>.\nВыберите план и свяжитесь с админом.",
        "en": "❌ You are currently a <b>regular user</b>.\nPick a plan and contact the admin.",
    },
    "vip_plans_title": {
        "uz": "\n💎 <b>VIP rejalar:</b>",
        "ru": "\n💎 <b>VIP планы:</b>",
        "en": "\n💎 <b>VIP plans:</b>",
    },
    "vip_benefits": {
        "uz": "\n🎁 <b>VIP imtiyozlari:</b>\n  • ⚡️ 24/7 avtomatik signallar (kanal + shaxsiy)\n  • 🎯 Faqat yuqori ishonchli (75%+) signallar\n  • 📊 Barcha juftliklar doimiy skanerlanadi\n  • 🔔 Tezkor TP/SL eslatmalari\n  • 👑 Ustuvor qo'llab-quvvatlash\n\n⚠️ <i>To'lovdan so'ng admin obunani faollashtiradi.</i>",
        "ru": "\n🎁 <b>Преимущества VIP:</b>\n  • ⚡️ Автосигналы 24/7 (канал + личные)\n  • 🎯 Только высокоуверенные (75%+) сигналы\n  • 📊 Постоянное сканирование всех пар\n  • 🔔 Быстрые напоминания TP/SL\n  • 👑 Приоритетная поддержка\n\n⚠️ <i>После оплаты админ активирует подписку.</i>",
        "en": "\n🎁 <b>VIP benefits:</b>\n  • ⚡️ 24/7 automatic signals (channel + private)\n  • 🎯 High-confidence (75%+) signals only\n  • 📊 Continuous scanning of all pairs\n  • 🔔 Fast TP/SL reminders\n  • 👑 Priority support\n\n⚠️ <i>Admin activates the subscription after payment.</i>",
    },
    "vip_status_ok": {
        "uz": "✅ VIP faol! Muddat: <b>{until}</b>",
        "ru": "✅ VIP активен! Действует до: <b>{until}</b>",
        "en": "✅ VIP active! Valid until: <b>{until}</b>",
    },
    "vip_status_no": {
        "uz": "❌ VIP obuna faol emas. Reja tanlang 👇",
        "ru": "❌ VIP подписка не активна. Выберите план 👇",
        "en": "❌ VIP subscription inactive. Choose a plan 👇",
    },
    "vip_unlimited_admin": {
        "uz": "Cheksiz (admin)",
        "ru": "Бессрочно (админ)",
        "en": "Unlimited (admin)",
    },
    "vip_plan_details": {
        "uz": "<b>To'lov tartibi:</b>\n1️⃣ Admin bilan bog'laning\n2️⃣ To'lovni amalga oshiring\n3️⃣ Telegram ID-ingizni yuboring: <code>{uid}</code>\n4️⃣ Obuna 5 daqiqa ichida faollashadi ✅\n\n⚠️ <i>Bot to'lovni qabul qilmaydi — faqat admin orqali.</i>",
        "ru": "<b>Порядок оплаты:</b>\n1️⃣ Свяжитесь с админом\n2️⃣ Произведите оплату\n3️⃣ Отправьте свой Telegram ID: <code>{uid}</code>\n4️⃣ Подписка активируется в течение 5 минут ✅\n\n⚠️ <i>Бот не принимает оплату — только через админа.</i>",
        "en": "<b>Payment steps:</b>\n1️⃣ Contact the admin\n2️⃣ Make the payment\n3️⃣ Send your Telegram ID: <code>{uid}</code>\n4️⃣ Subscription activates within 5 minutes ✅\n\n⚠️ <i>The bot does not accept payments — only via admin.</i>",
    },
    "vip_pay_admin_btn": {
        "uz": "💳 To'lov uchun admin",
        "ru": "💳 Админ для оплаты",
        "en": "💳 Admin for payment",
    },
    "vip_check_status": {
        "uz": "VIP holatimni tekshirish",
        "ru": "Проверить статус VIP",
        "en": "Check my VIP status",
    },
    "vip_plans_btn": {"uz": "💎 Rejalar", "ru": "💎 Планы", "en": "💎 Plans"},
    "plan_not_found": {
        "uz": "Reja topilmadi",
        "ru": "План не найден",
        "en": "Plan not found",
    },
    # ---------- signal formatlash ----------
    "overall_verdict": {
        "uz": "UMUMIY XULOSA",
        "ru": "ОБЩИЙ ВЫВОД",
        "en": "OVERALL VERDICT",
    },
    "confidence_lbl": {
        "uz": "Ishonch",
        "ru": "Уверенность",
        "en": "Confidence",
    },
    "winrate_lbl": {"uz": "Winrate Probability", "ru": "Вероятность Winrate", "en": "Winrate Probability"},
    "combined_score_lbl": {
        "uz": "Kombinatsiyalangan ball",
        "ru": "Комбинированный балл",
        "en": "Combined score",
    },
    "mtf_title": {
        "uz": "⏱ <b>Multi-Timeframe tahlili:</b>",
        "ru": "⏱ <b>Мультитаймфрейм анализ:</b>",
        "en": "⏱ <b>Multi-timeframe analysis:</b>",
    },
    "patterns_line": {
        "uz": "🕯 <b>Naqsh va figuralar:</b> {patterns}",
        "ru": "🕯 <b>Паттерны и фигуры:</b> {patterns}",
        "en": "🕯 <b>Patterns & figures:</b> {patterns}",
    },
    "levels_title": {
        "uz": "📐 <b>Darajalar (4H swing):</b>",
        "ru": "📐 <b>Уровни (свинг 4H):</b>",
        "en": "📐 <b>Levels (4H swing):</b>",
    },
    "near_resistance": {
        "uz": "🔻 Eng yaqin qarshilik",
        "ru": "🔻 Ближайшее сопротивление",
        "en": "🔻 Nearest resistance",
    },
    "near_support": {
        "uz": "🔺 Eng yaqin qo'llab-quvvatlash",
        "ru": "🔺 Ближайшая поддержка",
        "en": "🔺 Nearest support",
    },
    "neckline_lbl": {"uz": "bo'yin chizig'i", "ru": "линия шеи", "en": "neckline"},
    "trade_plan": {"uz": "SAVDYO REJASI", "ru": "ТОРГОВЫЙ ПЛАН", "en": "TRADE PLAN"},
    "entry_lbl": {"uz": "Entry", "ru": "Вход", "en": "Entry"},
    "sl_lbl": {"uz": "Stop Loss", "ru": "Стоп Лосс", "en": "Stop Loss"},
    "rr_total_lbl": {
        "uz": "Umumiy Risk/Reward",
        "ru": "Общий Risk/Reward",
        "en": "Overall Risk/Reward",
    },
    "risk_mgmt_title": {
        "uz": "💼 <b>Risk Management:</b>",
        "ru": "💼 <b>Риск-менеджмент:</b>",
        "en": "💼 <b>Risk Management:</b>",
    },
    "risk_max_line": {
        "uz": "• Bir savdada yo'qotish depozitning maksimal <b>{risk}%</b> idan oshmasin",
        "ru": "• Потеря в одной сделке не должна превышать <b>{risk}%</b> депозита",
        "en": "• Loss per trade should not exceed <b>{risk}%</b> of the deposit",
    },
    "position_size_line": {
        "uz": "• Tavsiya etilgan pozitsiya hajmi: depozitning ≈<b>{pct}%</b> ($100k depozit uchun {usd})",
        "ru": "• Рекомендуемый объём позиции: ≈<b>{pct}%</b> депозита (для $100к это {usd})",
        "en": "• Recommended position size: ≈<b>{pct}%</b> of deposit ({usd} for a $100k account)",
    },
    "size_calc_line": {
        "uz": "• Pozitsiya hajmini SL masofasiga qarab hisoblang",
        "ru": "• Рассчитайте объём позиции по расстоянию до SL",
        "en": "• Calculate position size based on SL distance",
    },
    "signal_quality_lbl": {
        "uz": "• Signal sifati: <b>{quality}</b>",
        "ru": "• Качество сигнала: <b>{quality}</b>",
        "en": "• Signal quality: <b>{quality}</b>",
    },
    "quality_high": {
        "uz": "Yuqori sifat ⭐️⭐️⭐️",
        "ru": "Высокое качество ⭐️⭐️⭐️",
        "en": "High quality ⭐️⭐️⭐️",
    },
    "quality_mid": {
        "uz": "O'rtacha sifat ⭐️⭐️",
        "ru": "Среднее качество ⭐️⭐️",
        "en": "Medium quality ⭐️⭐️",
    },
    "quality_low": {"uz": "Past sifat ⚠️", "ru": "Низкое качество ⚠️", "en": "Low quality ⚠️"},
    "disclaimer": {
        "uz": "⚠️ <i>Avtomatik tahlil — moliyaviy maslahat emas.</i>",
        "ru": "⚠️ <i>Автоматический анализ — не финансовая рекомендация.</i>",
        "en": "⚠️ <i>Automated analysis — not financial advice.</i>",
    },
    "neutral_zone": {
        "uz": "⚪️ <b>Neytral zona</b> — aniq yo'nalish yo'q, kutish tavsiya etiladi",
        "ru": "⚪️ <b>Нейтральная зона</b> — чёткого направления нет, рекомендуется ждать",
        "en": "⚪️ <b>Neutral zone</b> — no clear direction, waiting is advised",
    },
    "strength_line": {
        "uz": "[{bar}] Kuch: {score}%",
        "ru": "[{bar}] Сила: {score}%",
        "en": "[{bar}] Strength: {score}%",
    },
    "signals_hint": {
        "uz": "💡 Signallar odatda ball ±25 dan oshganda chiqariladi.",
        "ru": "💡 Сигналы обычно выдаются при балле выше ±25.",
        "en": "💡 Signals are usually issued when the score exceeds ±25.",
    },
    "current_price": {
        "uz": "💰 Joriy narx",
        "ru": "💰 Текущая цена",
        "en": "💰 Current price",
    },
    "patterns_none": {"uz": "Aniqlanmadi", "ru": "Не обнаружено", "en": "None detected"},
    "auto_header": {
        "uz": "⚡️ <b>AVTO-SIGNAL · {title}</b>",
        "ru": "⚡️ <b>АВТО-СИГНАЛ · {title}</b>",
        "en": "⚡️ <b>AUTO-SIGNAL · {title}</b>",
    },
    "not_advice_short": {
        "uz": "Moliyaviy maslahat emas",
        "ru": "Не финансовая рекомендация",
        "en": "Not financial advice",
    },
    "risk_deposit_lbl": {
        "uz": "Risk",
        "ru": "Риск",
        "en": "Risk",
    },
    "bull_state": {"uz": "Bullish ✅", "ru": "Бычий ✅", "en": "Bullish ✅"},
    "bear_state": {"uz": "Bearish ❌", "ru": "Медвежий ❌", "en": "Bearish ❌"},
    # ---------- price action ----------
    "pa_section": {
        "uz": "🧭 <b>Price Action tahlili:</b>",
        "ru": "🧭 <b>Price Action анализ:</b>",
        "en": "🧭 <b>Price action analysis:</b>",
    },
    "verdict_strong_buy": {
        "uz": "KUCHLI XARID",
        "ru": "СИЛЬНАЯ ПОКУПКА",
        "en": "STRONG BUY",
    },
    "verdict_buy": {"uz": "XARID", "ru": "ПОКУПКА", "en": "BUY"},
    "verdict_neutral": {"uz": "NEYTRAL", "ru": "НЕЙТРАЛЬНО", "en": "NEUTRAL"},
    "verdict_sell": {"uz": "SAVDO", "ru": "ПРОДАЖА", "en": "SELL"},
    "verdict_strong_sell": {
        "uz": "KUCHLI SAVDO",
        "ru": "СИЛЬНАЯ ПРОДАЖА",
        "en": "STRONG SELL",
    },
    "pa_structure": {
        "uz": "Bozor strukturası",
        "ru": "Структура рынка",
        "en": "Market structure",
    },
    "pa_liquidity": {
        "uz": "💧 Likvidlik: ↑ {above} · ↓ {below}",
        "ru": "💧 Ликвидность: ↑ {above} · ↓ {below}",
        "en": "💧 Liquidity: ↑ {above} · ↓ {below}",
    },
    "pa_sweep_bull": {
        "uz": "Pastki likvidlik surildi — stop-hunt tugadi (bullish)",
        "ru": "Нижняя ликвидность снята — стоп-хант завершён (бычье)",
        "en": "Sell-side liquidity swept — stop hunt done (bullish)",
    },
    "pa_sweep_bear": {
        "uz": "Yuqori likvidlik surildi — stop-hunt tugadi (bearish)",
        "ru": "Верхняя ликвидность снята — стоп-хант завершён (медвежье)",
        "en": "Buy-side liquidity swept — stop hunt done (bearish)",
    },
}

# naqsh nomlari (asl nomi -> tarjima; 'en' asl nomini oladi)
PATTERN_NAMES: dict[str, dict[str, str]] = {
    "Doji": {"uz": "Doji", "ru": "Доджи"},
    "Hammer": {"uz": "Bolg'a (Hammer)", "ru": "Молот (Hammer)"},
    "Inverted Hammer": {"uz": "Teskari bolg'a (Inverted Hammer)", "ru": "Перевёрнутый молот"},
    "Bullish Engulfing": {"uz": "Bullish Engulfing (yutuvchi)", "ru": "Бычье поглощение"},
    "Bearish Engulfing": {"uz": "Bearish Engulfing (yutuvchi)", "ru": "Медвежье поглощение"},
    "Morning Star": {"uz": "Morning Star (tong yulduzi)", "ru": "Утренняя звезда"},
    "Evening Star": {"uz": "Evening Star (kechki yulduz)", "ru": "Вечерняя звезда"},
    "Piercing Line": {"uz": "Piercing Line", "ru": "Заслон (Piercing Line)"},
    "Three White Soldiers": {"uz": "Uch oq askar", "ru": "Три белых солдата"},
    "Three Black Crows": {"uz": "Uch qora qarg'a", "ru": "Три чёрных ворона"},
    "Dark Cloud Cover": {"uz": "Qorong'i bulut (Dark Cloud Cover)", "ru": "Завеса тёмных облаков"},
    "Shooting Star": {"uz": "Shooting Star (otashfon yulduz)", "ru": "Падающая звезда"},
    "Hanging Man": {"uz": "Osilgan odam (Hanging Man)", "ru": "Повешенный"},
    "Head & Shoulders": {"uz": "Bosh va yelkalar", "ru": "Голова и плечи"},
    "Inverse Head & Shoulders": {
        "uz": "Teskari bosh va yelkalar",
        "ru": "Перевёрнутые голова и плечи",
    },
    "Double Top": {"uz": "Ikki toj (Double Top)", "ru": "Двойная вершина"},
    "Double Bottom": {"uz": "Ikki taglik (Double Bottom)", "ru": "Двойное дно"},
}


def pattern_name(name: str, lang: str | None) -> str:
    if lang == DEFAULT_LANG or lang not in SUPPORTED_LANGS:
        return name
    return PATTERN_NAMES.get(name, {}).get(lang, name)


def t(lang: str | None, key: str, **kwargs) -> str:
    """Kalit bo'yicha tilga mos matnni qaytaradi."""
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    entry = TEXTS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry[DEFAULT_LANG]
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def cache_lang(user_id: int, lang: str | None) -> None:
    if lang in SUPPORTED_LANGS:
        _lang_cache[user_id] = lang


def cached_lang(user_id: int) -> str | None:
    return _lang_cache.get(user_id)


def drop_cached_lang(user_id: int) -> None:
    _lang_cache.pop(user_id, None)


async def get_lang(user_id: int) -> str:
    """Foydalanuvchi tilini kesh/DB dan oladi (default uz)."""
    lang = cached_lang(user_id)
    if lang:
        return lang
    from database import db

    try:
        lang = await db.get_language(user_id)
    except Exception:
        lang = None
    return lang or DEFAULT_LANG
