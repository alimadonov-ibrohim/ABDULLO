import config
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import SUPPORTED_LANGS, t


def lang_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGS.items():
        kb.button(text=label, callback_data=f"lang:set:{code}")
    kb.adjust(1)
    return kb


def main_menu(lang: str = "uz", is_admin: bool = False) -> InlineKeyboardBuilder:
    """Ierarxiyali menyu: asosiy funksiya to'liq qatorda, qolganlari juftlikda."""
    price = next(iter(config.VIP_PLANS.values()))["price_usd"]
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "btn_pairs_list"), callback_data="pairs:list")
    kb.button(text=t(lang, "btn_vip_priced", price=price), callback_data="menu:vip")
    kb.button(text=t(lang, "btn_stats"), callback_data="menu:stats")
    kb.button(text=t(lang, "btn_signal_history"), callback_data="history:list")
    kb.button(text=t(lang, "btn_info"), callback_data="menu:info")
    kb.button(text=t(lang, "btn_help"), callback_data="menu:help")
    kb.button(
        text={"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"}.get(lang, "🌐 Til"),
        callback_data="lang:menu",
    )
    kb.button(
        text={"uz": "👑 Yaratuvchi", "ru": "👑 Создатель", "en": "👑 Creator"}.get(
            lang, "👑 Yaratuvchi"
        ),
        callback_data="menu:creator",
    )
    if is_admin:
        kb.button(text="🛠 Admin panel", callback_data="adm:panel")
    rows = (1, 2, 2, 2, 1) + ((1,) if is_admin else ())
    kb.adjust(*rows)
    return kb


def pairs_menu(lang: str = "uz") -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for pair in config.ALL_PAIRS:
        icon = "₿" if pair["screener"] == "crypto" else "$"
        kb.button(
            text=f"{icon} {pair['title']}",
            callback_data=f"analyze:{pair['symbol']}",
        )
    kb.button(text=t(lang, "btn_custom_pair"), callback_data="pairs:custom")
    kb.button(text=t(lang, "btn_back_main"), callback_data="menu:main")
    kb.adjust(2, 2, 2, 2, 1, 1)
    return kb


def after_analysis(symbol: str, lang: str = "uz") -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "btn_refresh"), callback_data=f"refresh:{symbol}")
    kb.button(
        text={
            "uz": "📋 Juftliklar",
            "ru": "📋 Пары",
            "en": "📋 Pairs",
        }.get(lang, "📋 Juftliklar"),
        callback_data="pairs:list",
    )
    kb.adjust(2)
    return kb


def history_back(lang: str = "uz") -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text={"uz": "🔙 Menyu", "ru": "🔙 Меню", "en": "🔙 Menu"}.get(lang, "🔙 Menyu"),
        callback_data="menu:main",
    )
    return kb


def vip_menu(lang: str = "uz", is_vip: bool = False) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for key, plan in config.VIP_PLANS.items():
        kb.button(
            text=f"{plan['label']} — ${plan['price_usd']}",
            callback_data=f"vip:plan:{key}",
        )
    mark = "✅" if is_vip else "❌"
    kb.button(
        text=f"{mark} {t(lang, 'vip_check_status')}", callback_data="vip:status"
    )
    kb.button(text=t(lang, "btn_back_main"), callback_data="menu:main")
    kb.adjust(1)
    return kb


def back_to_main(
    lang: str = "uz", extra: list[InlineKeyboardButton] | None = None
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if extra:
        for btn in extra:
            kb.row(btn)
    kb.button(text=t(lang, "btn_back_main"), callback_data="menu:main")
    kb.adjust(1)
    return kb


# ---------------- TO'LOV ----------------

def paid_confirm_kb(plan_key: str, lang: str) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "pay_i_paid_btn"), callback_data=f"vip:paid:{plan_key}")
    kb.button(text=t(lang, "btn_back_main"), callback_data="menu:vip")
    kb.adjust(1)
    return kb


def admin_payment_kb(payment_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"adm:vipok:{payment_id}")
    kb.button(text="❌ Bekor qilish", callback_data=f"adm:vipno:{payment_id}")
    kb.adjust(2)
    return kb


def pending_payments_kb(payments: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for p in payments:
        name = p.get("username") or p.get("full_name") or str(p["user_id"])
        kb.button(
            text=f"🧾 #{p['id']} · {name[:16]} · ${p['amount_usd']}",
            callback_data=f"adm:vipinfo:{p['id']}",
        )
    kb.button(text="🔄 Yangilash", callback_data="adm:pays")
    kb.button(text="🔙 Admin panel", callback_data="adm:panel")
    kb.adjust(1)
    return kb


# ---------------- ADMIN PANEL (o'zbek tilida) ----------------

def admin_panel_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 To'liq statistika", callback_data="adm:statsfull")
    kb.button(text="👥 Foydalanuvchilar", callback_data="adm:users")
    kb.button(text="💎 VIP obunachilar", callback_data="adm:vips")
    kb.button(text="🧾 To'lovlar", callback_data="adm:pays")
    kb.button(text="🚫 Bloklanganlar", callback_data="adm:banned")
    kb.button(text="📡 Broadcast", callback_data="adm:bcast")
    kb.button(text="⚡️ Skanerlash", callback_data="adm:scan")
    kb.button(text="🔙 Chiqish", callback_data="menu:main")
    kb.adjust(1)
    return kb


def users_list_kb(users: list[dict]) -> InlineKeyboardBuilder:
    """Foydalanuvchi kartasini ochadi (xavfsizroq — bir bosishda ban yo'q)."""
    kb = InlineKeyboardBuilder()
    for u in users:
        banned = bool(u["is_banned"])
        icon = "🚫" if banned else "✅"
        name = u.get("full_name") or u.get("username") or str(u["user_id"])
        kb.button(
            text=f"{icon} {name[:24]} ({u['user_id']})",
            callback_data=f"adm:userinfo:{u['user_id']}",
        )
    kb.button(text="🔄 Yangilash", callback_data="adm:users")
    kb.button(text="🔙 Admin panel", callback_data="adm:panel")
    kb.adjust(1)
    return kb


def user_detail_kb(user: dict) -> InlineKeyboardBuilder:
    uid = user["user_id"]
    banned = bool(user["is_banned"])
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Ban'dan chiqarish" if banned else "🚫 Bloklash",
        callback_data=f"adm:{'unban' if banned else 'ban'}:{uid}",
    )
    kb.button(text="💎 +7 kun VIP", callback_data=f"adm:vipgrant:{uid}:7")
    kb.button(text="💎 +30 kun VIP", callback_data=f"adm:vipgrant:{uid}:30")
    kb.button(text="❌ VIP olib tashlash", callback_data=f"adm:viprevoke:{uid}")
    kb.button(text="🔙 Ro'yxatga qaytish", callback_data="adm:users")
    kb.adjust(1, 2, 1, 1)
    return kb


def vips_list_kb(vips: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for v in vips:
        name = v.get("username") or v.get("full_name") or str(v["user_id"])
        kb.button(
            text=f"💎 {str(name)[:18]} · {v['days_left']} kun",
            callback_data=f"adm:userinfo:{v['user_id']}",
        )
    kb.button(text="🔄 Yangilash", callback_data="adm:vips")
    kb.button(text="🔙 Admin panel", callback_data="adm:panel")
    kb.adjust(1)
    return kb


def banned_list_kb(users: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for u in users:
        name = u.get("full_name") or u.get("username") or str(u["user_id"])
        kb.button(
            text=f"✅ {name[:24]} ({u['user_id']})",
            callback_data=f"adm:unban:{u['user_id']}",
        )
    kb.button(text="🔄 Yangilash", callback_data="adm:banned")
    kb.button(text="🔙 Admin panel", callback_data="adm:panel")
    kb.adjust(1)
    return kb


def admin_back_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin panel", callback_data="adm:panel")
    kb.adjust(1)
    return kb
