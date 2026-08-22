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
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "btn_pairs_list"), callback_data="pairs:list")
    kb.button(text=t(lang, "btn_vip_sub"), callback_data="menu:vip")
    kb.button(text=t(lang, "btn_signal_history"), callback_data="history:list")
    kb.button(text=t(lang, "btn_stats"), callback_data="menu:stats")
    kb.button(text=t(lang, "btn_help"), callback_data="menu:help")
    kb.button(text=t(lang, "btn_info"), callback_data="menu:info")
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
    rows = (2, 2, 2, 2) + ((1,) if is_admin else ())
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


# ---------------- ADMIN PANEL (o'zbek tilida) ----------------

def admin_panel_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 To'liq statistika", callback_data="adm:statsfull")
    kb.button(text="👥 Foydalanuvchilar", callback_data="adm:users")
    kb.button(text="🚫 Bloklanganlar", callback_data="adm:banned")
    kb.button(text="📡 Broadcast", callback_data="adm:bcast")
    kb.button(text="⚡️ Skanerlash", callback_data="adm:scan")
    kb.button(text="🔙 Chiqish", callback_data="menu:main")
    kb.adjust(1)
    return kb


def users_list_kb(users: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for u in users:
        banned = bool(u["is_banned"])
        icon = "✅" if banned else "🚫"
        action = "unban" if banned else "ban"
        name = u.get("full_name") or u.get("username") or str(u["user_id"])
        kb.button(
            text=f"{icon} {name[:24]} ({u['user_id']})",
            callback_data=f"adm:{action}:{u['user_id']}",
        )
    kb.button(text="🔄 Yangilash", callback_data="adm:users")
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
