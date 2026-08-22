import asyncio
import contextlib

import config
from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.types import CallbackQuery, Message
from database import db
from logger import get_logger
from utils.formatters import esc
from utils.i18n import get_lang, t
from utils.keyboards import (
    admin_back_kb,
    admin_panel_kb,
    banned_list_kb,
    users_list_kb,
)

log = get_logger("handlers.admin")

router = Router(name="admin")


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in config.ADMIN_IDS)


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ---------------- panel ----------------

async def _panel_text() -> str:
    total = await db.count_users()
    vip = len(await db.active_vip_user_ids())
    banned = await db.count_banned()
    return (
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"💎 VIP: <b>{vip}</b>\n"
        f"🚫 Bloklangan: <b>{banned}</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(await _panel_text(), reply_markup=admin_panel_kb().as_markup())


@router.callback_query(F.data == "adm:panel")
async def cb_panel(cb: CallbackQuery):
    await cb.message.edit_text(
        await _panel_text(), reply_markup=admin_panel_kb().as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "adm:statsfull")
async def cb_statsfull(cb: CallbackQuery):
    from handlers.start_menu import stats_text

    s = await db.stats_summary()
    vip = len(await db.active_vip_user_ids())
    lines = [
        "📊 <b>To'liq statistika</b>\n",
        f"👥 Foydalanuvchi: {s['total_users']} · 💎 VIP: {vip}",
        f"🚫 Bloklangan: {await db.count_banned()}",
        f"📡 Jami signallar: <b>{s['total_signals']}</b>",
        f"📅 Bugun: {s['today_signals']}",
        f"🟢 LONG: {s['buy']} · 🔴 SHORT: {s['sell']}",
        f"🎯 O'rtacha ishonch: {s['avg_confidence']}%",
    ]
    text = "\n".join(lines) + "\n\n" + await stats_text("uz")
    try:
        await cb.message.edit_text(text, reply_markup=admin_back_kb().as_markup())
    except Exception:
        await cb.message.answer(text, reply_markup=admin_back_kb().as_markup())
    await cb.answer()


@router.callback_query(F.data == "adm:bcast")
async def cb_bcast(cb: CallbackQuery):
    await cb.message.answer(
        "ℹ️ Broadcast uchun buyruqdan foydalaning:\n"
        "<code>/broadcast Xabar matni</code>\n"
        "<i>(HTML formatlash qo'llab-quvvatlanadi)</i>"
    )
    await cb.answer()


# ---------------- foydalanuvchilar / bloklash ----------------

def _user_line(u: dict) -> str:
    username = f"@{u['username']}" if u.get("username") else "-"
    status = "🚫 ban" if u["is_banned"] else "✅"
    return f"{status} <b>{esc(u.get('full_name') or '-')}</b> · {username} · <code>{u['user_id']}</code>"


@router.callback_query(F.data == "adm:users")
async def cb_users(cb: CallbackQuery):
    users = await db.recent_users(limit=10)
    lines = ["👥 <b>Oxirgi 10 foydalanuvchi:</b>\n"]
    lines.extend(_user_line(u) for u in users)
    lines.append("\nTugma bosilganda bloklanadi/ochiladi 👇")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=users_list_kb(users).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "adm:banned")
async def cb_banned_list(cb: CallbackQuery):
    users = await db.banned_users(limit=20)
    if not users:
        await cb.message.edit_text(
            "✅ Bloklangan foydalanuvchi yo'q.",
            reply_markup=admin_back_kb().as_markup(),
        )
        await cb.answer()
        return
    lines = [f"🚫 <b>Bloklanganlar ({len(users)}):</b>\n"]
    lines.extend(_user_line(u) for u in users)
    lines.append("\nOchish uchun tugmani bosing 👇")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=banned_list_kb(users).as_markup()
    )
    await cb.answer()


async def _notify_target(bot: Bot, user_id: int, action: str) -> None:
    """Blok/ochish haqida foydalanuvchiga uning tilida xabar yuboradi."""
    key = {"ban": "ban_notify", "unban": "unban_notify"}[action]
    try:
        lang = await get_lang(user_id)
        await bot.send_message(user_id, t(lang, key))
    except Exception:
        log.warning("ban notify failed for %s (%s)", user_id, action)


async def _render_users_list(cb: CallbackQuery) -> None:
    users = await db.recent_users(limit=10)
    lines = ["👥 <b>Oxirgi 10 foydalanuvchi:</b>\n"]
    lines.extend(_user_line(u) for u in users)
    lines.append("\nTugma bosilganda bloklanadi/ochiladi 👇")
    with contextlib.suppress(Exception):
        await cb.message.edit_text(
            "\n".join(lines), reply_markup=users_list_kb(users).as_markup()
        )


@router.callback_query(F.data.startswith("adm:ban:"))
async def cb_ban(cb: CallbackQuery):
    target_id = int(cb.data.rsplit(":", 1)[-1])
    ok = await db.set_banned(target_id, True)
    if ok:
        await _notify_target(cb.bot, target_id, "ban")
    await cb.answer(f"{'🚫 Bloklandi' if ok else '⚠️ Topilmadi'}: {target_id}", show_alert=True)
    await _render_users_list(cb)


@router.callback_query(F.data.startswith("adm:unban:"))
async def cb_unban(cb: CallbackQuery):
    target_id = int(cb.data.rsplit(":", 1)[-1])
    ok = await db.set_banned(target_id, False)
    if ok:
        await _notify_target(cb.bot, target_id, "unban")
    await cb.answer(f"{'✅ Ochildi' if ok else '⚠️ Topilmadi'}: {target_id}", show_alert=True)
    await _render_users_list(cb)


# ---------------- eski buyruqlar ----------------

@router.message(Command("addvip"))
async def cmd_addvip(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3 or not parts[1].lstrip("-").isdigit():
        await message.answer(
            "ℹ️ Foydalanish: <code>/addvip user_id kunlar_soni [plan]</code>\n"
            "Masalan: <code>/addvip 123456789 30 month</code>"
        )
        return
    target_id = int(parts[1])
    days = int(parts[2])
    plan = parts[3] if len(parts) > 3 else "manual"

    until = await db.set_vip(target_id, days, plan)
    await message.answer(
        f"✅ <b>{target_id}</b> uchun VIP yoqildi.\n"
        f"📅 Muddat: <b>{until[:16].replace('T', ' ')}</b> UTC ({days} kun, {esc(plan)})"
    )
    try:
        bot = message.bot
        await bot.send_message(
            target_id,
            f"💎 Tabriklaymiz! <b>VIP obuna</b> faollashtirildi!\n"
            f"📅 Amal qilish muddati: <b>{until[:16].replace('T', ' ')}</b> UTC\n"
            "⚡️ Endi avto-signallarni birinchi bo'lib olasiz!",
        )
    except Exception:
        log.warning("VIP notify failed for %s", target_id)


@router.message(Command("delvip"))
async def cmd_delvip(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("ℹ️ Foydalanish: <code>/delvip user_id</code>")
        return
    ok = await db.revoke_vip(int(parts[1]))
    await message.answer(
        "✅ VIP o'chirildi." if ok else "❌ Bu foydalanuvchida VIP topilmadi."
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    text = (message.text or "").partition(" ")[2].strip()
    if not text:
        await message.answer(
            "ℹ️ Foydalanish: <code>/broadcast xabar_matni</code>\n"
            "<i>(HTML formatlash qo'llab-quvvatlanadi)</i>"
        )
        return

    ids = await db.all_user_ids()
    sent = failed = 0
    status = await message.answer(f"📡 Yuborilmoqda... ({len(ids)} ta foydalanuvchi)")
    for uid in ids:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.06)
    await status.edit_text(
        f"📡 <b>Broadcast yakunlandi.</b>\n"
        f"✅ Yetkazildi: {sent}\n❌ Yetkazilmadi: {failed}"
    )


@router.message(Command("users"))
async def cmd_users(message: Message):
    total = await db.count_users()
    vip = len(await db.active_vip_user_ids())
    await message.answer(
        f"👥 <b>Jami:</b> {total}\n💎 <b>VIP:</b> {vip}\n"
        f"👤 Oddiy: {max(total - vip, 0)}\n🚫 Bloklangan: {await db.count_banned()}"
    )


@router.message(Command("statsfull"))
async def cmd_statsfull(message: Message):
    from handlers.start_menu import stats_text

    s = await db.stats_summary()
    vip = len(await db.active_vip_user_ids())
    lines = [
        "📊 <b>To'liq statistika</b>\n",
        f"👥 Foydalanuvchi: {s['total_users']} · 💎 VIP: {vip}",
        f"📡 Jami signallar: <b>{s['total_signals']}</b>",
        f"📅 Bugun: {s['today_signals']}",
        f"🟢 LONG: {s['buy']} · 🔴 SHORT: {s['sell']}",
        f"🎯 O'rtacha ishonch: {s['avg_confidence']}%\n",
    ]
    if s["top_symbols"]:
        lines.append("🏆 Top juftliklar:")
        for sym, cnt in s["top_symbols"].items():
            lines.append(f"  • {sym} — {cnt}")
    lines.append("\n" + await stats_text("uz"))
    await message.answer("\n".join(lines))


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("ℹ️ Foydalanish: <code>/ban user_id</code>")
        return
    target_id = int(parts[1])
    ok = await db.set_banned(target_id, True)
    if ok:
        await _notify_target(message.bot, target_id, "ban")
    await message.answer(f"🚫 <b>{parts[1]}</b> bloklandi.")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("ℹ️ Foydalanish: <code>/unban user_id</code>")
        return
    target_id = int(parts[1])
    ok = await db.set_banned(target_id, False)
    if ok:
        await _notify_target(message.bot, target_id, "unban")
    await message.answer(f"✅ <b>{parts[1]}</b> blokdan chiqarildi.")


@router.message(Command("scan"))
async def cmd_scan(message: Message):
    from scheduler import run_scan_cycle

    await message.answer("⚡️ Qo'lda skanerlash boshlandi...")
    try:
        count = await run_scan_cycle(message.bot)
        await message.answer(f"✅ Skaner tugadi. Yuborilgan signallar: <b>{count}</b>")
    except Exception:
        log.exception("manual scan failed")
        await message.answer("❌ Skanerda xatolik. Loglarni tekshiring.")
