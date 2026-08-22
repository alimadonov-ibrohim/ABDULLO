"""
Foydalanuvchilarning chat_id va tanlagan tilini saqlash/o'qish moduli.
Oddiy JSON fayl orqali saqlanadi - bot qayta ishga tushsa ham eslab qoladi.
"""
import json
import os

if os.environ.get("VERCEL"):
    _BASE_DIR = "/tmp"
else:
    _BASE_DIR = os.path.dirname(__file__)

USERS_FILE = os.path.join(_BASE_DIR, "users.json")


def load_users() -> dict:
    """{'123456789': {'lang': 'uz'}, ...} formatida qaytaradi."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def set_user_language(chat_id: str, lang: str):
    users = load_users()
    chat_id = str(chat_id)
    if chat_id not in users:
        users[chat_id] = {}
    users[chat_id]["lang"] = lang
    save_users(users)


def get_user_language(chat_id: str, default: str = "uz") -> str:
    users = load_users()
    return users.get(str(chat_id), {}).get("lang", default)


def get_all_registered_chat_ids() -> list:
    """Tilni tanlagan barcha foydalanuvchilar chat_id ro'yxati (signal yuborish uchun)."""
    users = load_users()
    return list(users.keys())


def get_all_users() -> dict:
    """Barcha foydalanuvchilar ma'lumotlarini to'liq qaytaradi."""
    return load_users()


def get_user_symbols(chat_id: str, default: list) -> list:
    """Foydalanuvchi tanlagan juftliklar. Tanlanmagan bo'lsa — standart ro'yxat."""
    symbols = load_users().get(str(chat_id), {}).get("symbols")
    if not symbols:
        return list(default)
    if isinstance(symbols, str):
        return [symbols]
    return list(symbols)


def toggle_user_symbol(chat_id: str, symbol: str, default: list) -> bool:
    """Juftlikni tanlanganlar ro'yxatiga qo'shadi/olib tashlaydi.
    Qaytaradi: True = qo'shildi, False = olib tashlandi."""
    users = load_users()
    chat_id = str(chat_id)
    info = users.setdefault(chat_id, {})
    current = info.get("symbols")
    current = list(current) if current else list(default)

    if symbol in current:
        current.remove(symbol)
        added = False
    else:
        current.append(symbol)
        added = True

    info["symbols"] = current
    save_users(users)
    return added
