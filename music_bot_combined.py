#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎵 Music & Video Telegram Bot — BITTA FAYLGA BIRLASHTIRILGAN VERSIYA
=====================================================================
Asl loyiha quyidagi fayllardan iborat edi:
    bot.py, config.py, database.py, downloader.py,
    handlers/start.py, handlers/music.py, handlers/admin.py,
    utils/keyboards.py

Barchasi shu bitta fayl ichiga jamlandi. Ishga tushirish:
    pip install -r requirements.txt
    python music_bot_combined.py

⚠️ Eslatma: utils/keyboards.py loyihada import qilingan, lekin
   yuklangan fayllar orasida yo'q edi. Quyida u bot.py/music.py/
   admin.py dagi chaqiruvlar (tugma nomlari, callback_data'lar)
   asosida qayta tiklandi — funksionallik saqlanadi.
"""

import os
import sys
import logging
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

# Windows konsolida emoji loglarni chiqarish uchun
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
#   ⚙️  CONFIG
# ============================================================

# ✅ BU YERGA O'Z BOT TOKENINGIZNI KIRITING
BOT_TOKEN = "8990014554:AAF1mcRScK00peC9RZLi9KkrU43wiDS95y4"

ADMIN_IDS = [8260383196]  # Bir nechta: [123456789, 987654321]

# ✅ LOG CHANNEL (xatolar shu yerga yoziladi, ixtiyoriy)
LOG_CHANNEL_ID = None  # masalan: -1001234567890

# ✅ START RASM URL (ixtiyoriy)
START_IMAGE_URL = None

# Database fayli
DB_PATH = "bot_database.db"

# Yuklab olish papkasi
DOWNLOAD_PATH = "downloads/"

# Maksimal fayl hajmi (Telegram limiti: 50MB)
MAX_FILE_SIZE_MB = 50

# Bir foydalanuvchi kuniga maksimal yuklab olish soni
MAX_DOWNLOADS_PER_DAY = 20

# Bot versiyasi
BOT_VERSION = "2.0.0"

# Bot nomi
BOT_NAME = "🎵 Music & Video Bot"

# Til
LANGUAGE = "uz"  # uz yoki ru


# ============================================================
#   🗄️  DATABASE
# ============================================================


def get_db():
    """Database ulanishini qaytaradi"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Barcha jadvallarni yaratadi"""
    conn = get_db()
    cursor = conn.cursor()

    # ─── Foydalanuvchilar jadvali ─────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            full_name    TEXT,
            join_date    TEXT DEFAULT (date('now')),
            last_active  TEXT DEFAULT (datetime('now')),
            is_banned    INTEGER DEFAULT 0,
            is_admin     INTEGER DEFAULT 0,
            downloads    INTEGER DEFAULT 0,
            lang         TEXT DEFAULT 'uz'
        )
    """)

    # ─── Majburiy kanallar jadvali ────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id   TEXT UNIQUE NOT NULL,
            channel_name TEXT,
            channel_link TEXT,
            added_date   TEXT DEFAULT (datetime('now')),
            is_active    INTEGER DEFAULT 1
        )
    """)

    # ─── Reklamalar jadvali ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id     INTEGER,
            message_text TEXT,
            sent_count   INTEGER DEFAULT 0,
            fail_count   INTEGER DEFAULT 0,
            sent_date    TEXT DEFAULT (datetime('now')),
            status       TEXT DEFAULT 'pending'
        )
    """)

    # ─── Qidiruv tarixi ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            query        TEXT,
            search_date  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ─── Yuklab olishlar tarixi ───────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloads_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            title        TEXT,
            url          TEXT,
            file_type    TEXT,
            download_date TEXT DEFAULT (datetime('now'))
        )
    """)

    # ─── Bot statistikasi ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date    TEXT UNIQUE DEFAULT (date('now')),
            new_users    INTEGER DEFAULT 0,
            searches     INTEGER DEFAULT 0,
            downloads    INTEGER DEFAULT 0
        )
    """)

    # ─── Bot sozlamalari ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default sozlamalar
    defaults = [
        ("welcome_text", "🎵 Xush kelibsiz! Qo'shiq yoki video qidiring."),
        ("search_enabled", "1"),
        ("download_enabled", "1"),
        ("maintenance_mode", "0"),
    ]
    for key, value in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()
    logger.info("✅ Database muvaffaqiyatli ishga tushdi")


# ─── FOYDALANUVCHI FUNKSIYALARI ────────────────────────────────────────────

def add_user(user_id: int, username: str, full_name: str):
    """Yangi foydalanuvchi qo'shadi yoki yangilaydi"""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = datetime('now')
        """, (user_id, username, full_name))

        # Statistika yangilash
        conn.execute("""
            INSERT INTO stats (stat_date, new_users) VALUES (date('now'), 1)
            ON CONFLICT(stat_date) DO UPDATE SET new_users = new_users + 1
        """)
        conn.commit()
    finally:
        conn.close()


def get_user(user_id: int):
    """Foydalanuvchi ma'lumotlarini qaytaradi"""
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_all_users(active_only=False):
    """Barcha foydalanuvchilarni qaytaradi"""
    conn = get_db()
    try:
        if active_only:
            return conn.execute(
                "SELECT user_id FROM users WHERE is_banned = 0"
            ).fetchall()
        return conn.execute("SELECT * FROM users").fetchall()
    finally:
        conn.close()


def ban_user(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def unban_user(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user["is_banned"])


def is_admin(user_id: int, config_admins: list) -> bool:
    if user_id in config_admins:
        return True
    user = get_user(user_id)
    return bool(user and user["is_admin"])


def add_admin(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def remove_admin(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def increment_downloads(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
    conn.execute("""
        INSERT INTO stats (stat_date, downloads) VALUES (date('now'), 1)
        ON CONFLICT(stat_date) DO UPDATE SET downloads = downloads + 1
    """)
    conn.commit()
    conn.close()


def log_download(user_id: int, title: str, url: str, file_type: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO downloads_log (user_id, title, url, file_type) VALUES (?, ?, ?, ?)",
        (user_id, title, url, file_type)
    )
    conn.commit()
    conn.close()


def log_search(user_id: int, query: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
        (user_id, query)
    )
    conn.execute("""
        INSERT INTO stats (stat_date, searches) VALUES (date('now'), 1)
        ON CONFLICT(stat_date) DO UPDATE SET searches = searches + 1
    """)
    conn.commit()
    conn.close()


# ─── KANAL FUNKSIYALARI ────────────────────────────────────────────────────

def add_channel(channel_id: str, channel_name: str, channel_link: str):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_link) VALUES (?, ?, ?)",
            (channel_id, channel_name, channel_link)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Kanal qo'shishda xato: {e}")
        return False
    finally:
        conn.close()


def remove_channel(channel_id: str):
    conn = get_db()
    conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()


def get_channels():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM channels WHERE is_active = 1"
        ).fetchall()
    finally:
        conn.close()


# ─── STATISTIKA ────────────────────────────────────────────────────────────

def get_stats():
    conn = get_db()
    try:
        total_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
        active_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_banned = 0").fetchone()["cnt"]
        banned_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_banned = 1").fetchone()["cnt"]
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_admin = 1").fetchone()["cnt"]
        total_downloads = conn.execute("SELECT SUM(downloads) as total FROM users").fetchone()["total"] or 0
        channel_count = conn.execute("SELECT COUNT(*) as cnt FROM channels WHERE is_active = 1").fetchone()["cnt"]

        today_stats = conn.execute(
            "SELECT * FROM stats WHERE stat_date = date('now')"
        ).fetchone()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "admin_count": admin_count,
            "total_downloads": total_downloads,
            "channel_count": channel_count,
            "today_new_users": today_stats["new_users"] if today_stats else 0,
            "today_searches": today_stats["searches"] if today_stats else 0,
            "today_downloads": today_stats["downloads"] if today_stats else 0,
        }
    finally:
        conn.close()


# ─── SOZLAMALAR ────────────────────────────────────────────────────────────

def get_setting(key: str, default=None):
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


# ============================================================
#   ⌨️  KEYBOARDS
# ============================================================

def main_menu() -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi menyusi"""
    buttons = [
        ["🎵 Musiqa qidirish", "🎬 Video qidirish"],
        ["📋 Playlist", "🔥 Trend"],
        ["ℹ️ Ma'lumot"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    """Admin panel menyusi"""
    buttons = [
        ["📊 Statistika", "👥 Foydalanuvchilar"],
        ["📢 Reklama", "📡 Kanallar"],
        ["🔧 Sozlamalar"],
        ["🏠 Asosiy menyu"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def subscription_keyboard(channels: list) -> InlineKeyboardMarkup:
    """Majburiy obuna kanallari + tekshirish tugmasi"""
    buttons = []
    for ch in channels:
        link = ch.get("channel_link") or f"https://t.me/{str(ch.get('channel_id', '')).lstrip('@')}"
        buttons.append([InlineKeyboardButton(f"📢 {ch.get('channel_name', 'Kanal')}", url=link)])
    buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(buttons)


def close_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Yopish", callback_data="close")]])


def back_button(callback_data: str = "admin_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=callback_data)]])


def confirm_keyboard(yes_data: str, no_data: str = "close") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ha", callback_data=yes_data),
        InlineKeyboardButton("❌ Yo'q", callback_data=no_data),
    ]])


def search_results_keyboard(results: list, mode: str = "audio") -> InlineKeyboardMarkup:
    """Qidiruv natijalari ro'yxati uchun tugmalar"""
    buttons = []
    for i, item in enumerate(results):
        title = item.get("title", "Nomsiz")[:35]
        buttons.append([
            InlineKeyboardButton(f"{i + 1}. {title}", callback_data=f"select_{mode}_{i}")
        ])
    buttons.append([InlineKeyboardButton("❌ Yopish", callback_data="close")])
    return InlineKeyboardMarkup(buttons)


def download_options_keyboard(video_id: str, title: str = "") -> InlineKeyboardMarkup:
    """Yuklab olish formati tanlash tugmalari"""
    buttons = [
        [InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"dl_audio_{video_id}")],
        [InlineKeyboardButton("🔊 Voice (Ovozli xabar)", callback_data=f"dl_voice_{video_id}")],
        [
            InlineKeyboardButton("📹 360p", callback_data=f"dl_video_360_{video_id}"),
            InlineKeyboardButton("📹 480p", callback_data=f"dl_video_480_{video_id}"),
        ],
        [
            InlineKeyboardButton("📹 720p", callback_data=f"dl_video_720_{video_id}"),
            InlineKeyboardButton("📹 1080p", callback_data=f"dl_video_1080_{video_id}"),
        ],
        [
            InlineKeyboardButton("🔙 Natijalarga qaytish", callback_data="back_to_results"),
            InlineKeyboardButton("❌ Yopish", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_refresh_stats")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")],
    ])


def admin_users_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban qilish", callback_data="admin_ban_user")],
        [InlineKeyboardButton("✅ Banni olish", callback_data="admin_unban_user")],
        [InlineKeyboardButton("👑 Admin qo'shish", callback_data="admin_add_admin")],
        [InlineKeyboardButton("🔻 Adminlikdan olish", callback_data="admin_remove_admin")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")],
    ])


def admin_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton("🗑 Kanal o'chirish", callback_data="admin_remove_channel")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")],
    ])


def admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Hammaga", callback_data="broadcast_all")],
        [InlineKeyboardButton("✅ Aktiv userlarga", callback_data="broadcast_active")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")],
    ])


def admin_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Qidiruv yoq/o'chir", callback_data="setting_search")],
        [InlineKeyboardButton("⬇️ Yuklash yoq/o'chir", callback_data="setting_download")],
        [InlineKeyboardButton("🔧 Texnik ish rejimi", callback_data="setting_maintenance")],
        [InlineKeyboardButton("📝 Xush kelibsiz matni", callback_data="setting_welcome")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_menu")],
    ])


# ============================================================
#   ⬇️  DOWNLOADER (yt-dlp)
# ============================================================


# Downloads papkasini yaratish
Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)


async def search_youtube(query: str, max_results: int = 8) -> list:
    """
    YouTube'dan video qidiradi
    Qaytaradi: [{'title', 'url', 'duration', 'thumbnail', 'channel', 'views'}]
    """
    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        search_url = f"ytsearch{max_results}:{query}"

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: _extract_info(search_url, ydl_opts))

        if not results or 'entries' not in results:
            return []

        items = []
        for entry in results['entries']:
            if not entry:
                continue
            duration = entry.get('duration', 0)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"

            items.append({
                'title': entry.get('title', 'Nomsiz'),
                'url': f"https://youtube.com/watch?v={entry.get('id', '')}",
                'video_id': entry.get('id', ''),
                'duration': duration_str,
                'thumbnail': entry.get('thumbnail', ''),
                'channel': entry.get('uploader', 'Noma\'lum'),
                'views': _format_views(entry.get('view_count', 0)),
            })

        return items

    except Exception as e:
        logger.error(f"Qidiruv xatosi: {e}")
        return []


def _extract_info(url, opts):
    import yt_dlp
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _format_views(views):
    if not views:
        return "?"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


async def get_video_info(url: str) -> dict:
    """Video haqida to'liq ma'lumot oladi"""
    try:
        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
        }
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: _extract_info(url, opts))
        return info or {}
    except Exception as e:
        logger.error(f"Video info xatosi: {e}")
        return {}


async def download_audio(url: str, user_id: int) -> tuple:
    """
    Audio yuklab oladi (MP3)
    Qaytaradi: (file_path, title, duration) yoki (None, None, None)
    """
    output_path = os.path.join(DOWNLOAD_PATH, f"audio_{user_id}_%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'max_filesize': MAX_FILE_SIZE_MB * 1024 * 1024,
    }

    try:
        import yt_dlp
        loop = asyncio.get_event_loop()

        info = {}

        def _download():
            nonlocal info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

        await loop.run_in_executor(None, _download)

        if not info:
            return None, None, None

        # Fayl yo'lini topish
        video_id = info.get('id', '')
        file_path = os.path.join(DOWNLOAD_PATH, f"audio_{user_id}_{video_id}.mp3")

        if not os.path.exists(file_path):
            # Boshqa nom bilan qidirish
            for f in os.listdir(DOWNLOAD_PATH):
                if f.startswith(f"audio_{user_id}") and f.endswith('.mp3'):
                    file_path = os.path.join(DOWNLOAD_PATH, f)
                    break

        if not os.path.exists(file_path):
            return None, None, None

        title = info.get('title', 'Audio')
        duration = info.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"

        return file_path, title, duration_str

    except Exception as e:
        logger.error(f"Audio yuklab olish xatosi: {e}")
        return None, None, None


async def download_video(url: str, user_id: int, quality: str = "720") -> tuple:
    """
    Video yuklab oladi (MP4)
    Qaytaradi: (file_path, title, duration) yoki (None, None, None)
    """
    output_path = os.path.join(DOWNLOAD_PATH, f"video_{user_id}_%(id)s.%(ext)s")

    # Sifat tanlash
    format_map = {
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    }
    fmt = format_map.get(quality, "bestvideo[height<=720]+bestaudio/best")

    ydl_opts = {
        'format': fmt,
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'max_filesize': MAX_FILE_SIZE_MB * 1024 * 1024,
    }

    try:
        import yt_dlp
        loop = asyncio.get_event_loop()
        info = {}

        def _download():
            nonlocal info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

        await loop.run_in_executor(None, _download)

        if not info:
            return None, None, None

        video_id = info.get('id', '')
        file_path = os.path.join(DOWNLOAD_PATH, f"video_{user_id}_{video_id}.mp4")

        if not os.path.exists(file_path):
            for f in os.listdir(DOWNLOAD_PATH):
                if f.startswith(f"video_{user_id}") and f.endswith('.mp4'):
                    file_path = os.path.join(DOWNLOAD_PATH, f)
                    break

        if not os.path.exists(file_path):
            return None, None, None

        title = info.get('title', 'Video')
        duration = info.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"

        # Fayl hajmini tekshirish
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            os.remove(file_path)
            logger.warning(f"Fayl juda katta: {file_size / 1024 / 1024:.1f}MB")
            return None, "TOO_LARGE", None

        return file_path, title, duration_str

    except Exception as e:
        logger.error(f"Video yuklab olish xatosi: {e}")
        return None, None, None


async def get_playlist_info(url: str) -> dict:
    """Playlist ma'lumotlarini oladi"""
    try:
        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: _extract_info(url, opts))

        if not info:
            return {}

        entries = info.get('entries', [])
        return {
            'title': info.get('title', 'Playlist'),
            'uploader': info.get('uploader', 'Noma\'lum'),
            'count': len(entries),
            'videos': [
                {
                    'title': e.get('title', 'Nomsiz'),
                    'url': f"https://youtube.com/watch?v={e.get('id', '')}",
                    'duration': e.get('duration', 0),
                }
                for e in entries[:20] if e  # Maksimal 20 ta
            ]
        }
    except Exception as e:
        logger.error(f"Playlist xatosi: {e}")
        return {}


def cleanup_file(file_path: str):
    """Vaqtinchalik faylni o'chiradi"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Fayl o'chirishda xato: {e}")


def cleanup_user_files(user_id: int):
    """Foydalanuvchi fayllarini tozalaydi"""
    try:
        for f in os.listdir(DOWNLOAD_PATH):
            if f.startswith(f"audio_{user_id}") or f.startswith(f"video_{user_id}"):
                os.remove(os.path.join(DOWNLOAD_PATH, f))
    except Exception as e:
        logger.error(f"Tozalashda xato: {e}")


# ============================================================
#   🚀  START HANDLER
# ============================================================


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi /start bosganida"""
    user = update.effective_user

    # Foydalanuvchini bazaga qo'shish
    add_user(user.id, user.username or "", user.full_name)

    # Ban tekshirish
    if is_banned(user.id):
        await update.message.reply_text(
            "🚫 Siz botdan foydalanishingiz taqiqlangan.\n"
            "Murojaat uchun adminlarga yozing."
        )
        return

    # Texnik ish rejimi
    if get_setting("maintenance_mode") == "1" and user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "🔧 Bot hozirda texnik ish rejimida.\n"
            "Iltimos, keyinroq urinib ko'ring."
        )
        return

    # Majburiy obuna tekshirish
    not_subscribed = await check_subscriptions(user.id, context)
    if not_subscribed:
        channels = get_channels()
        channel_list = [dict(ch) for ch in channels]
        await update.message.reply_text(
            "👋 Xush kelibsiz!\n\n"
            "🔒 Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:\n\n"
            "📢 Obuna bo'lib, '✅ Tekshirish' tugmasini bosing:",
            reply_markup=subscription_keyboard(channel_list)
        )
        return

    # Xush kelibsiz xabari
    welcome_text = get_setting("welcome_text", "🎵 Xush kelibsiz!")

    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        f"{welcome_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎵 Musiqa qidirish - Qo'shiq nomini yozing\n"
        "🎬 Video - YouTube video linki yuboring\n"
        "📋 Playlist - Playlist linkini yuboring\n"
        "━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    await update.message.reply_text(
        "📖 <b>BOT QO'LLANMASI</b>\n\n"
        "🔍 <b>Qidirish:</b>\n"
        "• Qo'shiq nomini yuboring → musiqa topadi\n"
        "• YouTube link → yuklab beradi\n\n"
        "🎵 <b>Audio:</b>\n"
        "• MP3 formatida yuklab beradi\n"
        "• Ovozli xabar (Voice) sifatida\n\n"
        "🎬 <b>Video:</b>\n"
        "• 360p, 480p, 720p, 1080p sifatlarda\n\n"
        "📋 <b>Playlist:</b>\n"
        "• YouTube playlist linkini yuboring\n"
        "• Playlist videolari ro'yxatini ko'ring\n\n"
        "⚙️ <b>Buyruqlar:</b>\n"
        "/start - Botni boshlash\n"
        "/help - Yordam\n"
        "/stats - Statistika",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot haqida"""

    stats = get_stats()

    await update.message.reply_text(
        f"ℹ️ <b>{BOT_NAME}</b>\n\n"
        f"📊 Bot statistikasi:\n"
        f"• Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"• Aktiv foydalanuvchilar: <b>{stats['active_users']}</b>\n"
        f"• Jami yuklashlar: <b>{stats['total_downloads']}</b>\n\n"
        f"🔢 Versiya: <b>v{BOT_VERSION}</b>",
        parse_mode="HTML"
    )


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obuna tekshirish tugmasi bosilganda"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    not_subscribed = await check_subscriptions(user_id, context)

    if not_subscribed:
        channels = get_channels()
        channel_list = [dict(ch) for ch in channels]
        await query.edit_message_text(
            "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!\n\n"
            "Quyidagi barcha kanallarga obuna bo'ling, so'ng qaytadan tekshiring:",
            reply_markup=subscription_keyboard(channel_list)
        )
    else:
        await query.edit_message_text("✅ Ajoyib! Endi botdan foydalanishingiz mumkin.")

        welcome_text = get_setting("welcome_text", "🎵 Xush kelibsiz!")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Xush kelibsiz!\n\n{welcome_text}",
            reply_markup=main_menu()
        )


async def check_subscriptions(user_id: int, context) -> list:
    """
    Foydalanuvchi barcha majburiy kanallarga obuna bo'lganini tekshiradi
    Qaytaradi: obuna bo'lmagan kanallar ro'yxati
    """
    channels = get_channels()
    not_subscribed = []

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel["channel_id"],
                user_id=user_id
            )
            if member.status in ["left", "kicked", "banned"]:
                not_subscribed.append(dict(channel))
        except Exception as e:
            logger.error(f"Kanal tekshirishda xato {channel['channel_id']}: {e}")
            # Xato bo'lsa, o'tkazib yuboramiz

    return not_subscribed


# ============================================================
#   🎵  MUSIC HANDLER
# ============================================================


# Foydalanuvchi sessiyalari (RAM)
user_sessions = {}  # {user_id: {'results': [...], 'mode': 'audio'/'video'}}


async def _check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Foydalanuvchi ruxsatini tekshiradi"""
    user = update.effective_user

    if is_banned(user.id):
        await update.message.reply_text("🚫 Siz ban qilingansiz.")
        return False

    not_subscribed = await check_subscriptions(user.id, context)
    if not_subscribed:
        channels = get_channels()
        channel_list = [dict(ch) for ch in channels]
        await update.message.reply_text(
            "🔒 Botdan foydalanish uchun kanallarga obuna bo'ling:",
            reply_markup=subscription_keyboard(channel_list)
        )
        return False

    return True


async def handle_music_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎵 Musiqa qidirish tugmasi"""
    await update.message.reply_text(
        "🎵 <b>Musiqa qidirish</b>\n\n"
        "Qo'shiq nomini yozing:\n"
        "Misol: <code>Shohruhxon yig'la</code>",
        parse_mode="HTML"
    )
    user_sessions[update.effective_user.id] = {'mode': 'audio', 'results': []}


async def handle_video_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎬 Video qidirish tugmasi"""
    await update.message.reply_text(
        "🎬 <b>Video qidirish</b>\n\n"
        "Video nomini yozing yoki YouTube linkini yuboring:\n"
        "Misol: <code>BTS Dynamite</code>",
        parse_mode="HTML"
    )
    user_sessions[update.effective_user.id] = {'mode': 'video', 'results': []}


async def handle_playlist_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Playlist tugmasi"""
    await update.message.reply_text(
        "📋 <b>YouTube Playlist</b>\n\n"
        "Playlist linkini yuboring:\n"
        "Misol: <code>https://youtube.com/playlist?list=...</code>",
        parse_mode="HTML"
    )
    user_sessions[update.effective_user.id] = {'mode': 'playlist', 'results': []}


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn xabarini qayta ishlash (qidiruv yoki link)"""
    if not await _check_access(update, context):
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {'mode': 'audio'})

    # YouTube link tekshirish
    if "youtube.com" in text or "youtu.be" in text:
        if "playlist" in text:
            await handle_playlist_link(update, context, text)
        else:
            await handle_youtube_link(update, context, text)
        return

    # Matn orqali qidiruv
    mode = session.get('mode', 'audio')
    if mode not in ("audio", "video"):
        mode = "audio"
    await search_music(update, context, text, mode)


async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, mode: str = "audio"):
    """YouTube'dan qidiruv"""
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # Yuklanish xabari
    msg = await update.message.reply_text(f"🔍 <b>'{query}'</b> qidirilmoqda...", parse_mode="HTML")

    # Qidirish
    results = await search_youtube(query, max_results=8)
    log_search(user_id, query)

    if not results:
        await msg.edit_text(
            "❌ Natija topilmadi.\n\n"
            "Boshqa kalit so'zlar bilan urinib ko'ring.",
            reply_markup=close_button()
        )
        return

    # Sessiyaga saqlash
    user_sessions[user_id] = {'mode': mode, 'results': results, 'query': query}

    # Natijalarni ko'rsatish
    text = f"🎵 <b>'{query}'</b> uchun natijalar:\n\n"
    for i, item in enumerate(results):
        emoji = "🎵" if mode == "audio" else "🎬"
        text += f"{emoji} <b>{i + 1}.</b> {item['title'][:50]}\n"
        text += f"   ⏱ {item['duration']} | 👁 {item.get('views', '?')} | 📺 {item.get('channel', '')[:20]}\n\n"

    await msg.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=search_results_keyboard(results, mode)
    )


async def handle_result_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qidiruv natijasidan tanlash"""
    query = update.callback_query
    await query.answer()

    data = query.data  # select_audio_0 yoki select_video_2
    parts = data.split("_")
    mode = parts[1]
    idx = int(parts[2])

    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    results = session.get('results', [])

    if not results or idx >= len(results):
        await query.edit_message_text("❌ Xato: natija topilmadi.")
        return

    item = results[idx]
    video_id = item.get('video_id', '')
    title = item.get('title', 'Noma\'lum')
    url = item.get('url', '')
    duration = item.get('duration', '?')
    channel = item.get('channel', '')

    # Sessiyga tanlangan elementni saqlash
    user_sessions[user_id]['selected'] = item
    user_sessions[user_id]['selected_url'] = url

    text = (
        f"🎵 <b>{title}</b>\n\n"
        f"📺 Kanal: {channel}\n"
        f"⏱ Davomiyligi: {duration}\n\n"
        f"🔗 <a href='{url}'>YouTube'da ko'rish</a>\n\n"
        f"Quyidagi formatlardan birini tanlang:"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=download_options_keyboard(video_id, title),
        disable_web_page_preview=True
    )


async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yuklab olish - callback orqali"""
    query = update.callback_query
    await query.answer("⏳ Yuklanmoqda...")

    data = query.data
    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    selected = session.get('selected', {})
    url = session.get('selected_url', '')

    if not url:
        # Callback data dan URL olish harakat
        parts = data.split("_")
        if len(parts) >= 3:
            short_id = "_".join(parts[2:] if len(parts) > 3 else [parts[-1]])
            url = f"https://youtube.com/watch?v={short_id}"

    if not url:
        await query.edit_message_text("❌ URL topilmadi.")
        return

    title = selected.get('title', 'Fayl')

    if data.startswith("dl_audio_") or data.startswith("dl_voice_"):
        is_voice = data.startswith("dl_voice_")
        await _download_audio(query, context, url, user_id, title, is_voice)

    elif data.startswith("dl_video_"):
        parts = data.split("_")
        quality = parts[2] if len(parts) > 2 else "720"
        await _download_video(query, context, url, user_id, title, quality)


async def _download_audio(query, context, url: str, user_id: int, title: str, as_voice: bool = False):
    """Audio yuklash va yuborish"""
    await query.edit_message_text(
        f"⬇️ <b>{'Ovozli xabar' if as_voice else 'Audio'}</b> yuklanmoqda...\n\n"
        f"🎵 {title}\n\n"
        f"⏳ Iltimos kuting (30-60 soniya)...",
        parse_mode="HTML"
    )

    await context.bot.send_chat_action(
        chat_id=user_id,
        action=ChatAction.UPLOAD_VOICE if as_voice else ChatAction.UPLOAD_DOCUMENT
    )

    file_path, dl_title, duration = await download_audio(url, user_id)

    if not file_path:
        await query.edit_message_text(
            "❌ Yuklab olishda xato!\n\n"
            "Mumkin sabablar:\n"
            "• Fayl juda katta (50MB dan oshadi)\n"
            "• Video cheklangan yoki o'chirilgan\n"
            "• Internet ulanish muammosi",
            reply_markup=close_button()
        )
        return

    try:
        caption = (
            f"🎵 <b>{dl_title or title}</b>\n"
            f"⏱ Davomiyligi: {duration}\n\n"
            f"📱 @{context.bot.username}"
        )

        with open(file_path, 'rb') as f:
            if as_voice:
                await context.bot.send_voice(
                    chat_id=user_id,
                    voice=f,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=f,
                    title=dl_title or title,
                    caption=caption,
                    parse_mode="HTML"
                )

        increment_downloads(user_id)
        log_download(user_id, dl_title or title, url, "voice" if as_voice else "audio")

        await query.edit_message_text(
            f"✅ <b>Muvaffaqiyatli yuborildi!</b>\n\n🎵 {dl_title or title}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Audio yuborishda xato: {e}")
        await query.edit_message_text(
            f"❌ Yuborishda xato: {str(e)[:100]}",
            reply_markup=close_button()
        )
    finally:
        cleanup_file(file_path)


async def _download_video(query, context, url: str, user_id: int, title: str, quality: str = "720"):
    """Video yuklash va yuborish"""
    await query.edit_message_text(
        f"⬇️ <b>Video ({quality}p)</b> yuklanmoqda...\n\n"
        f"🎬 {title}\n\n"
        f"⏳ Iltimos kuting (1-3 daqiqa)...",
        parse_mode="HTML"
    )

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.UPLOAD_VIDEO)

    file_path, dl_title, duration = await download_video(url, user_id, quality)

    if not file_path:
        if dl_title == "TOO_LARGE":
            await query.edit_message_text(
                f"❌ Video juda katta! (50MB limitdan oshadi)\n\n"
                f"Pastroq sifat tanlang: 360p yoki 480p",
                reply_markup=close_button()
            )
        else:
            await query.edit_message_text(
                "❌ Video yuklab olishda xato!\n\n"
                "• Fayl juda katta bo'lishi mumkin\n"
                "• Pastroq sifat tanlang",
                reply_markup=close_button()
            )
        return

    try:
        caption = (
            f"🎬 <b>{dl_title or title}</b>\n"
            f"📹 Sifat: {quality}p\n"
            f"⏱ Davomiyligi: {duration}\n\n"
            f"📱 @{context.bot.username}"
        )

        with open(file_path, 'rb') as f:
            await context.bot.send_video(
                chat_id=user_id,
                video=f,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True
            )

        increment_downloads(user_id)
        log_download(user_id, dl_title or title, url, f"video_{quality}p")

        await query.edit_message_text(
            f"✅ <b>Video muvaffaqiyatli yuborildi!</b>\n\n🎬 {dl_title or title}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Video yuborishda xato: {e}")
        await query.edit_message_text(
            f"❌ Yuborishda xato: {str(e)[:100]}",
            reply_markup=close_button()
        )
    finally:
        cleanup_file(file_path)


async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """YouTube linki yuborilganda"""
    user_id = update.effective_user.id

    msg = await update.message.reply_text("🔍 Video ma'lumotlari olinmoqda...")

    info = await get_video_info(url)

    if not info:
        await msg.edit_text("❌ Bu video topilmadi yoki mavjud emas.")
        return

    title = info.get('title', 'Noma\'lum')
    duration = info.get('duration', 0)
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"
    channel = info.get('uploader', 'Noma\'lum')
    views = info.get('view_count') or 0

    video_id = info.get('id', '')

    user_sessions[user_id] = {
        'mode': 'video',
        'selected': {'title': title, 'video_id': video_id},
        'selected_url': url
    }

    text = (
        f"🎬 <b>{title}</b>\n\n"
        f"📺 Kanal: {channel}\n"
        f"⏱ Davomiyligi: {duration_str}\n"
        f"👁 Ko'rishlar: {views:,}\n\n"
        f"Yuklab olish formatini tanlang:"
    )

    await msg.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=download_options_keyboard(video_id, title)
    )


async def handle_playlist_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Playlist linki yuborilganda"""
    msg = await update.message.reply_text("📋 Playlist ma'lumotlari olinmoqda...")

    info = await get_playlist_info(url)

    if not info or not info.get('videos'):
        await msg.edit_text("❌ Bu playlist topilmadi yoki bo'sh.")
        return

    title = info.get('title', 'Playlist')
    uploader = info.get('uploader', 'Noma\'lum')
    count = info.get('count', 0)
    videos = info.get('videos', [])

    text = f"📋 <b>{title}</b>\n"
    text += f"👤 Muallif: {uploader}\n"
    text += f"🎬 Jami: {count} ta video\n\n"
    text += "📝 <b>Birinchi 20 ta video:</b>\n\n"

    for i, video in enumerate(videos[:20], 1):
        duration = video.get('duration', 0)
        dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"
        v_title = video.get('title', 'Nomsiz')[:45]
        text += f"{i}. {v_title} [{dur_str}]\n"

    buttons = []
    for i, video in enumerate(videos[:5]):
        v_title = video.get('title', 'Nomsiz')[:30]
        v_url = video.get('url', '')
        # URL dan video ID olish
        vid_id = v_url.split('v=')[-1][:11] if 'v=' in v_url else ''
        if vid_id:
            buttons.append([
                InlineKeyboardButton(
                    f"⬇️ {i + 1}. {v_title}",
                    callback_data=f"pl_dl_{vid_id}"
                )
            ])

    buttons.append([InlineKeyboardButton("❌ Yopish", callback_data="close")])

    await msg.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_playlist_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Playlist'dan video tanlanganda (pl_dl_ callback)"""
    query = update.callback_query
    await query.answer()

    vid_id = query.data.replace("pl_dl_", "")
    url = f"https://youtube.com/watch?v={vid_id}"
    user_id = query.from_user.id

    user_sessions[user_id] = {
        'mode': 'video',
        'selected': {'title': 'Video', 'video_id': vid_id},
        'selected_url': url
    }

    await query.edit_message_text(
        "🎬 Video yuklash uchun formatni tanlang:",
        reply_markup=download_options_keyboard(vid_id)
    )


async def handle_trend_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔥 Trend musiqalar"""
    msg = await update.message.reply_text("🔥 Trend musiqalar qidirilmoqda...")

    results = await search_youtube("top trending music 2025", max_results=8)

    if not results:
        await msg.edit_text("❌ Trend musiqalar topilmadi.")
        return

    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'audio', 'results': results}

    text = "🔥 <b>Trend Musiqalar</b>\n\n"
    for i, item in enumerate(results):
        text += f"🎵 <b>{i + 1}.</b> {item['title'][:50]}\n"
        text += f"   ⏱ {item['duration']} | 👁 {item.get('views', '?')}\n\n"

    await msg.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=search_results_keyboard(results, "audio")
    )


async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarni yopish"""
    query = update.callback_query
    await query.answer()
    await query.delete_message()


async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Natijalar ro'yxatiga qaytish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    results = session.get('results', [])
    mode = session.get('mode', 'audio')
    qry = session.get('query', '')

    if not results:
        await query.edit_message_text("❌ Natijalar topilmadi.")
        return

    text = f"🎵 <b>'{qry}'</b> uchun natijalar:\n\n"
    for i, item in enumerate(results):
        emoji = "🎵" if mode == "audio" else "🎬"
        text += f"{emoji} <b>{i + 1}.</b> {item['title'][:50]}\n"
        text += f"   ⏱ {item['duration']}\n\n"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=search_results_keyboard(results, mode)
    )


# ============================================================
#   👑  ADMIN HANDLER
# ============================================================


# ConversationHandler holatlari
(
    WAITING_BROADCAST_MSG,
    WAITING_BAN_ID,
    WAITING_UNBAN_ID,
    WAITING_CHANNEL_ID,
    WAITING_CHANNEL_NAME,
    WAITING_CHANNEL_LINK,
    WAITING_WELCOME_TEXT,
    WAITING_ADD_ADMIN,
    WAITING_REMOVE_ADMIN,
) = range(9)

# Vaqtinchalik ma'lumotlar
admin_state = {}


def is_admin_user(user_id: int) -> bool:
    """Admin ekanligini tekshiradi"""
    if user_id in ADMIN_IDS:
        return True
    user = get_user(user_id)
    return bool(user and user["is_admin"])


# ─── ADMIN BUYRUQLARI ────────────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneliga kirish"""
    user_id = update.effective_user.id

    if not is_admin_user(user_id):
        await update.message.reply_text("❌ Sizda admin huquqi yo'q.")
        return

    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\n"
        "Xush kelibsiz, admin!\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# ─── STATISTIKA ─────────────────────────────────────────────────────────

async def handle_stats_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Statistika"""
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    stats = get_stats()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    text = (
        f"📊 <b>BOT STATISTIKASI</b>\n"
        f"<i>Yangilangan: {now}</i>\n\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"  • Jami: <b>{stats['total_users']}</b>\n"
        f"  • Aktiv: <b>{stats['active_users']}</b>\n"
        f"  • Banlangan: <b>{stats['banned_users']}</b>\n"
        f"  • Adminlar: <b>{stats['admin_count']}</b>\n\n"
        f"📅 <b>Bugungi faollik:</b>\n"
        f"  • Yangi foydalanuvchilar: <b>{stats['today_new_users']}</b>\n"
        f"  • Qidiruvlar: <b>{stats['today_searches']}</b>\n"
        f"  • Yuklab olishlar: <b>{stats['today_downloads']}</b>\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  • Jami yuklab olishlar: <b>{stats['total_downloads']}</b>\n"
        f"  • Majburiy kanallar: <b>{stats['channel_count']}</b>"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_stats_keyboard()
    )


# ─── FOYDALANUVCHILAR ────────────────────────────────────────────────────

async def handle_users_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👥 Foydalanuvchilar boshqaruvi"""
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    stats = get_stats()
    text = (
        f"👥 <b>FOYDALANUVCHILAR BOSHQARUVI</b>\n\n"
        f"📊 Jami: <b>{stats['total_users']}</b>\n"
        f"✅ Aktiv: <b>{stats['active_users']}</b>\n"
        f"🚫 Banlangan: <b>{stats['banned_users']}</b>\n\n"
        f"Amalni tanlang:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_users_keyboard()
    )


async def ban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban qilish - foydalanuvchi ID so'rash"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    admin_state[query.from_user.id] = {'action': 'ban', 'msg_id': query.message.message_id}

    await query.edit_message_text(
        "🚫 <b>Foydalanuvchini ban qilish</b>\n\n"
        "Foydalanuvchi ID sini yuboring:\n"
        "<i>Masalan: 123456789</i>\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_BAN_ID


async def unban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban olish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    admin_state[query.from_user.id] = {'action': 'unban'}

    await query.edit_message_text(
        "✅ <b>Foydalanuvchi banini olish</b>\n\n"
        "Foydalanuvchi ID sini yuboring:\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_UNBAN_ID


async def process_ban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban ID ni qayta ishlash"""
    user_id = update.effective_user.id
    state = admin_state.get(user_id, {})

    try:
        target_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID. Raqam kiriting.")
        return WAITING_BAN_ID

    action = state.get('action')
    if action == 'ban':
        ban_user(target_id)
        await update.message.reply_text(
            f"✅ Foydalanuvchi <b>{target_id}</b> banlandi.",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
        # Foydalanuvchiga xabar
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🚫 Siz botdan foydalanish huquqidan mahrum etildingiz."
            )
        except Exception:
            pass
    elif action == 'unban':
        unban_user(target_id)
        await update.message.reply_text(
            f"✅ Foydalanuvchi <b>{target_id}</b> bani olindi.",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="✅ Sizning ban holatingiz bekor qilindi. Endi botdan foydalanishingiz mumkin."
            )
        except Exception:
            pass

    del admin_state[user_id]
    return ConversationHandler.END


async def add_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin qo'shish"""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Faqat bosh admin bu amalni bajarishi mumkin!", show_alert=True)
        return

    admin_state[query.from_user.id] = {'action': 'add_admin'}
    await query.edit_message_text(
        "👑 <b>Admin qo'shish</b>\n\n"
        "Yangi admin ID sini yuboring:\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_ADD_ADMIN


async def process_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi admin ID qayta ishlash"""
    try:
        target_id = int(update.message.text.strip())
        add_admin(target_id)
        await update.message.reply_text(
            f"✅ Foydalanuvchi <b>{target_id}</b> admin qilindi.",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="👑 Siz admin qildingiz! /admin buyrug'ini bosing."
            )
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID.")
        return WAITING_ADD_ADMIN

    return ConversationHandler.END


async def remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adminlikdan olish"""
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Faqat bosh admin!", show_alert=True)
        return

    admin_state[query.from_user.id] = {'action': 'remove_admin'}
    await query.edit_message_text(
        "🔻 <b>Adminlikdan olish</b>\n\n"
        "Admin ID sini yuboring:\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_REMOVE_ADMIN


async def process_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text.strip())
        remove_admin(target_id)
        await update.message.reply_text(
            f"✅ Foydalanuvchi <b>{target_id}</b> adminlikdan olindi.",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID.")
        return WAITING_REMOVE_ADMIN

    return ConversationHandler.END


# ─── KANALLAR BOSHQARUVI ─────────────────────────────────────────────────

async def handle_channels_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📡 Kanallar boshqaruvi"""
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    channels = get_channels()
    text = f"📡 <b>KANALLAR BOSHQARUVI</b>\n\n"
    text += f"Aktiv kanallar: <b>{len(channels)}</b>\n\n"

    if channels:
        text += "📋 <b>Ro'yxat:</b>\n"
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['channel_name']} ({ch['channel_id']})\n"
    else:
        text += "⚠️ Hali hech qanday kanal qo'shilmagan."

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_channels_keyboard()
    )


async def add_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal qo'shish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    admin_state[query.from_user.id] = {'action': 'add_channel', 'step': 'id'}

    await query.edit_message_text(
        "➕ <b>Yangi kanal qo'shish</b>\n\n"
        "<b>1-qadam:</b> Kanal ID ni yuboring\n"
        "Misol: <code>@kanalnomlari</code> yoki <code>-1001234567890</code>\n\n"
        "⚠️ Botni kanalga admin qiling, keyin bu amalni bajaring!\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_CHANNEL_ID


async def process_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal ID qayta ishlash"""
    user_id = update.effective_user.id
    channel_id = update.message.text.strip()

    if not channel_id.startswith('@') and not channel_id.startswith('-'):
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n"
            "Misol: @kanal_nomi yoki -1001234567890"
        )
        return WAITING_CHANNEL_ID

    admin_state[user_id]['channel_id'] = channel_id
    admin_state[user_id]['step'] = 'name'

    await update.message.reply_text(
        "✅ Kanal ID qabul qilindi!\n\n"
        "<b>2-qadam:</b> Kanal nomini yuboring\n"
        "Misol: <code>Mening Kanalim</code>",
        parse_mode="HTML"
    )
    return WAITING_CHANNEL_NAME


async def process_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal nomi"""
    user_id = update.effective_user.id
    admin_state[user_id]['channel_name'] = update.message.text.strip()

    await update.message.reply_text(
        "✅ Kanal nomi qabul qilindi!\n\n"
        "<b>3-qadam:</b> Kanal invite linkini yuboring\n"
        "Misol: <code>https://t.me/kanalnomlari</code>",
        parse_mode="HTML"
    )
    return WAITING_CHANNEL_LINK


async def process_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal linki va saqlash"""
    user_id = update.effective_user.id
    channel_link = update.message.text.strip()

    state = admin_state.get(user_id, {})
    channel_id = state.get('channel_id', '')
    channel_name = state.get('channel_name', '')

    if not channel_link.startswith('http'):
        await update.message.reply_text("❌ Noto'g'ri link. https:// bilan boshlanishi kerak.")
        return WAITING_CHANNEL_LINK

    # Kanal tekshirish
    try:
        chat = await context.bot.get_chat(channel_id)
        success = add_channel(channel_id, channel_name, channel_link)

        if success:
            await update.message.reply_text(
                f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
                f"📢 Nomi: {channel_name}\n"
                f"🔗 ID: {channel_id}\n"
                f"📎 Link: {channel_link}",
                parse_mode="HTML",
                reply_markup=admin_menu()
            )
        else:
            await update.message.reply_text("❌ Kanal qo'shishda xato.", reply_markup=admin_menu())

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kanal topilmadi!\n\n"
            f"Botni kanalga admin qilib qo'ying, keyin qaytadan urinib ko'ring.\n"
            f"Xato: {str(e)[:100]}",
            reply_markup=admin_menu()
        )

    if user_id in admin_state:
        del admin_state[user_id]

    return ConversationHandler.END


async def remove_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal o'chirish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    channels = get_channels()
    if not channels:
        await query.edit_message_text("❌ Hech qanday kanal yo'q.")
        return

    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                f"🗑 {ch['channel_name']}",
                callback_data=f"del_channel_{ch['channel_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_channels")])

    await query.edit_message_text(
        "🗑 <b>O'chirish uchun kanal tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def delete_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanalini o'chirish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    channel_id = query.data.replace("del_channel_", "")
    remove_channel(channel_id)

    await query.edit_message_text(
        f"✅ Kanal <b>{channel_id}</b> o'chirildi.",
        parse_mode="HTML",
        reply_markup=admin_channels_keyboard()
    )


# ─── REKLAMA / BROADCAST ─────────────────────────────────────────────────

async def handle_broadcast_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📢 Reklama yuborish"""
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    stats = get_stats()
    await update.message.reply_text(
        f"📢 <b>REKLAMA / BROADCAST</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"✅ Aktiv foydalanuvchilar: <b>{stats['active_users']}</b>\n\n"
        f"Reklama turini tanlang:",
        parse_mode="HTML",
        reply_markup=admin_broadcast_keyboard()
    )


async def broadcast_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hammaga reklama yuborish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    admin_state[query.from_user.id] = {'action': 'broadcast', 'target': 'all'}

    await query.edit_message_text(
        "📢 <b>Barcha foydalanuvchilarga reklama</b>\n\n"
        "Reklama xabarini yuboring:\n"
        "• Matn, rasm, video, audio - barchasi qabul qilinadi\n"
        "• HTML formatida yozishingiz mumkin\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_BROADCAST_MSG


async def broadcast_active_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aktiv foydalanuvchilarga reklama"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    admin_state[query.from_user.id] = {'action': 'broadcast', 'target': 'active'}

    await query.edit_message_text(
        "📢 <b>Aktiv foydalanuvchilarga reklama</b>\n\n"
        "Reklama xabarini yuboring:\n\n"
        "/cancel - bekor qilish",
        parse_mode="HTML"
    )
    return WAITING_BROADCAST_MSG


async def process_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reklamani yuborish"""
    admin_id = update.effective_user.id
    state = admin_state.get(admin_id, {})
    target = state.get('target', 'all')

    msg = await update.message.reply_text(
        "⏳ Reklama yuborilmoqda...\n"
        "Iltimos kuting, bu biroz vaqt oladi."
    )

    users = get_all_users(active_only=(target == 'active'))

    sent = 0
    failed = 0
    total = len(users)

    for i, user_row in enumerate(users):
        user_id = user_row['user_id']

        try:
            # Reklama xabarini copy qilib yuborish
            await update.message.copy(chat_id=user_id)
            sent += 1
        except Exception:
            failed += 1

        # Har 50 ta foydalanuvchida progress yangilash
        if (i + 1) % 50 == 0:
            try:
                await msg.edit_text(
                    f"⏳ Yuborilmoqda...\n"
                    f"✅ {sent} | ❌ {failed} | Qoldi: {total - i - 1}"
                )
            except Exception:
                pass

        # Anti-spam uchun kichik kutish
        if i % 30 == 0:
            await asyncio.sleep(1)

    if admin_id in admin_state:
        del admin_state[admin_id]

    await msg.edit_text(
        f"✅ <b>Reklama muvaffaqiyatli yuborildi!</b>\n\n"
        f"📊 Natijalar:\n"
        f"  • Jami: <b>{total}</b>\n"
        f"  • Yuborildi: <b>{sent}</b>\n"
        f"  • Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )

    return ConversationHandler.END


# ─── SOZLAMALAR ──────────────────────────────────────────────────────────

async def handle_settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔧 Sozlamalar"""
    user_id = update.effective_user.id
    if not is_admin_user(user_id):
        return

    search = "✅ Yoqilgan" if get_setting("search_enabled") == "1" else "❌ O'chirilgan"
    download = "✅ Yoqilgan" if get_setting("download_enabled") == "1" else "❌ O'chirilgan"
    maintenance = "🔧 Yoqilgan" if get_setting("maintenance_mode") == "1" else "✅ O'chirilgan"

    await update.message.reply_text(
        f"🔧 <b>BOT SOZLAMALARI</b>\n\n"
        f"🔍 Qidiruv: {search}\n"
        f"⬇️ Yuklab olish: {download}\n"
        f"🔧 Texnik ish: {maintenance}\n\n"
        f"O'zgartirish uchun tugmani bosing:",
        parse_mode="HTML",
        reply_markup=admin_settings_keyboard()
    )


async def toggle_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sozlamani yoqish/o'chirish"""
    query = update.callback_query
    await query.answer()

    if not is_admin_user(query.from_user.id):
        return

    data = query.data

    setting_map = {
        "setting_search": "search_enabled",
        "setting_download": "download_enabled",
        "setting_maintenance": "maintenance_mode",
    }

    if data == "setting_welcome":
        admin_state[query.from_user.id] = {'action': 'welcome'}
        await query.edit_message_text(
            "📝 Yangi xush kelibsiz matnini yuboring:\n\n"
            "/cancel - bekor qilish"
        )
        return WAITING_WELCOME_TEXT

    key = setting_map.get(data)
    if key:
        current = get_setting(key, "1")
        new_value = "0" if current == "1" else "1"
        set_setting(key, new_value)

        status = "✅ Yoqildi" if new_value == "1" else "❌ O'chirildi"
        await query.answer(f"{status}", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=admin_settings_keyboard())


async def process_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xush kelibsiz matnini saqlash"""
    set_setting("welcome_text", update.message.text)
    await update.message.reply_text(
        "✅ Xush kelibsiz matni yangilandi!",
        reply_markup=admin_menu()
    )
    return ConversationHandler.END


# ─── CANCEL ──────────────────────────────────────────────────────────────

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Amalni bekor qilish"""
    user_id = update.effective_user.id
    if user_id in admin_state:
        del admin_state[user_id]

    await update.message.reply_text(
        "❌ Bekor qilindi.",
        reply_markup=admin_menu() if is_admin_user(user_id) else main_menu()
    )
    return ConversationHandler.END


# ─── INLINE CALLBACKS ────────────────────────────────────────────────────

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin callback larni qayta ishlash"""
    query = update.callback_query

    if not is_admin_user(query.from_user.id):
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    data = query.data

    if data == "admin_menu":
        await query.answer()
        await query.edit_message_text(
            "👑 Admin panel",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Statistika", callback_data="admin_refresh_stats")],
                [InlineKeyboardButton("📡 Kanallar", callback_data="admin_channels")],
            ])
        )

    elif data == "admin_refresh_stats":
        await query.answer("Yangilanmoqda...")
        stats = get_stats()
        text = (
            f"📊 <b>Statistika</b>\n\n"
            f"👥 Jami: {stats['total_users']}\n"
            f"✅ Aktiv: {stats['active_users']}\n"
            f"📥 Jami yuklashlar: {stats['total_downloads']}"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=admin_stats_keyboard())

    elif data == "admin_channels":
        channels = get_channels()
        text = f"📡 Kanallar: {len(channels)} ta"
        await query.edit_message_text(text, reply_markup=admin_channels_keyboard())


# ============================================================
#   🤖  MAIN BOT (Application yaratish va ishga tushirish)
# ============================================================


def create_admin_conversation() -> ConversationHandler:
    """Admin ConversationHandler yaratish"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ban_user_callback, pattern="^admin_ban_user$"),
            CallbackQueryHandler(unban_user_callback, pattern="^admin_unban_user$"),
            CallbackQueryHandler(add_channel_callback, pattern="^admin_add_channel$"),
            CallbackQueryHandler(broadcast_all_callback, pattern="^broadcast_all$"),
            CallbackQueryHandler(broadcast_active_callback, pattern="^broadcast_active$"),
            CallbackQueryHandler(toggle_setting_callback, pattern="^setting_welcome$"),
            CallbackQueryHandler(add_admin_callback, pattern="^admin_add_admin$"),
            CallbackQueryHandler(remove_admin_callback, pattern="^admin_remove_admin$"),
        ],
        states={
            WAITING_BAN_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban_id)
            ],
            WAITING_UNBAN_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban_id)
            ],
            WAITING_CHANNEL_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_channel_id)
            ],
            WAITING_CHANNEL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_channel_name)
            ],
            WAITING_CHANNEL_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_channel_link)
            ],
            WAITING_BROADCAST_MSG: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.VIDEO |
                     filters.AUDIO | filters.Document.ALL) & ~filters.COMMAND,
                    process_broadcast_message
                )
            ],
            WAITING_WELCOME_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_welcome_text)
            ],
            WAITING_ADD_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin)
            ],
            WAITING_REMOVE_ADMIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_admin)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
        ],
        per_user=True,
        per_chat=True,
        per_message=True,
    )


async def error_handler(update: object, context) -> None:
    """Global xato ushlagich"""
    logger.error(f"Xato: {context.error}", exc_info=context.error)

    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Xato yuz berdi. Iltimos, qaytadan urinib ko'ring."
            )
        except Exception:
            pass


def main():
    """Botni ishga tushirish"""
    # Database ishga tushirish
    init_db()
    logger.info("🚀 Bot ishga tushirilmoqda...")

    # Application yaratish
    app = Application.builder().token(BOT_TOKEN).build()

    # ─── BUYRUQLAR ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("stats", info_command))

    # ─── ADMIN PANEL (Conversation) ───────────────────────────────────────
    app.add_handler(create_admin_conversation())

    # ─── CALLBACK HANDLERS ────────────────────────────────────────────────
    # Obuna tekshirish
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))

    # Musiqa natijalari
    app.add_handler(CallbackQueryHandler(handle_result_selection, pattern="^select_(audio|video)_\\d+$"))

    # Playlist video tanlash
    app.add_handler(CallbackQueryHandler(handle_playlist_download, pattern="^pl_dl_"))

    # Yuklab olish
    app.add_handler(CallbackQueryHandler(handle_download, pattern="^dl_(audio|voice|video)_"))

    # Yopish / Orqaga
    app.add_handler(CallbackQueryHandler(close_callback, pattern="^close$"))
    app.add_handler(CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"))

    # Admin callbacks
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_(menu|refresh_stats|channels)$"))
    app.add_handler(CallbackQueryHandler(remove_channel_callback, pattern="^admin_remove_channel$"))
    app.add_handler(CallbackQueryHandler(delete_channel_callback, pattern="^del_channel_"))
    app.add_handler(CallbackQueryHandler(broadcast_all_callback, pattern="^broadcast_all$"))
    app.add_handler(CallbackQueryHandler(broadcast_active_callback, pattern="^broadcast_active$"))
    app.add_handler(CallbackQueryHandler(toggle_setting_callback, pattern="^setting_"))

    # ─── TUGMA HANDLERLARI ────────────────────────────────────────────────
    # Admin tugmalari
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📊 Statistika$"),
        handle_stats_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^👥 Foydalanuvchilar$"),
        handle_users_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📢 Reklama$"),
        handle_broadcast_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📡 Kanallar$"),
        handle_channels_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔧 Sozlamalar$"),
        handle_settings_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🏠 Asosiy menyu$"),
        start_command
    ))

    # Foydalanuvchi tugmalari
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🎵 Musiqa qidirish$"),
        handle_music_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🎬 Video qidirish$"),
        handle_video_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📋 Playlist$"),
        handle_playlist_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔥 Trend$"),
        handle_trend_button
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^ℹ️ Ma'lumot$"),
        info_command
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^⬇️ Yuklab olish$"),
        handle_video_button
    ))

    # Matn xabarlari (qidiruv)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))

    # ─── XATO HANDLER ──────────────────────────────────────────────────────
    app.add_error_handler(error_handler)

    # ─── BOTNI ISHGA TUSHIRISH ─────────────────────────────────────────────
    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    logger.info(f"👑 Admin IDlar: {ADMIN_IDS}")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
