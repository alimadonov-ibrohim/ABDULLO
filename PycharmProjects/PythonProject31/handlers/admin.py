import asyncio
import contextlib
from datetime import datetime, timezone

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
    user_detail_kb,
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
    try:
        trial = await db.count_trials()
    except Exception:
        log.exception("count_trials failed")
        trial = 0
    pending = await db.count_pending_payments()
    return (
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"💎 VIP: <b>{vip}</b>\n"
        f"🎁 Sinov (trial): <b>{trial}</b>\n"
        f"🧾 Kutilayotgan to'lov: <b>{pending}</b>\n"
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


# ---------------- to'lovlar ----------------

def _payment_line(p: dict) -> str:
    uname = f"@{p['username']}" if p.get("username") else "-"
    return (
        f"🧾 <b>Buyurtma #{p['id']}</b>\n"
        f"👤 {esc(p['full_name'] or '-')} · {uname}\n"
        f"🆔 <code>{p['user_id']}</code>\n"
        f"💎 Plan: <b>{esc(p['plan'])}</b> — ${p['amount_usd']} · "
        f"{'⭐️ Stars' if p['method'] == 'stars' else '👨‍💼 Qo\'lda'}\n"
        f"🕒 {p['created_at'][:16].replace('T', ' ')} UTC"
    )


async def _approve_payment(cb: CallbackQuery, pid: int) -> None:
    p = await db.get_payment(pid)
    if not p or p["status"] != "pending":
        await cb.answer("⚠️ Buyurtma topilmadi yoki allaqachon yopilgan.", show_alert=True)
        return
    plan = config.VIP_PLANS.get(p["plan"])
    days = plan["days"] if plan else 30
    await db.set_payment_status(pid, "approved", resolved_by=cb.from_user.id)
    from handlers.vip import activate_vip_and_notify

    until = await activate_vip_and_notify(cb.bot, p["user_id"], p["plan"], "manual")
    await cb.message.edit_text(
        f"✅ #{pid} tasdiqlandi!\n💎 VIP: <code>{p['user_id']}</code>\n"
        f"📅 Muddat: {until[:16].replace('T', ' ')} UTC"
    )
    log.info("Payment #%s approved by %s", pid, cb.from_user.id)
    await cb.answer("✅ VIP faollashtirildi")


@router.callback_query(F.data.startswith("adm:vipok:"))
async def cb_vip_approve(cb: CallbackQuery):
    await _approve_payment(cb, int(cb.data.rsplit(":", 1)[-1]))


@router.callback_query(F.data.startswith("adm:vipno:"))
async def cb_vip_reject(cb: CallbackQuery):
    pid = int(cb.data.rsplit(":", 1)[-1])
    ok = await db.set_payment_status(pid, "rejected", resolved_by=cb.from_user.id)
    if not ok:
        await cb.answer("⚠️ Buyurtma topilmadi.", show_alert=True)
        return
    p = await db.get_payment(pid)
    try:
        lang = await get_lang(p["user_id"]) if p else "uz"
        if p:
            await cb.bot.send_message(p["user_id"], t(lang, "pay_rejected"))
    except Exception:
        log.warning("reject notify failed for %s", p and p["user_id"])
    await cb.message.edit_text(f"❌ #{pid} bekor qilindi.")
    await cb.answer("❌ Bekor qilindi")


@router.callback_query(F.data == "adm:pays")
async def cb_payments(cb: CallbackQuery):
    from utils.keyboards import pending_payments_kb

    pays = await db.pending_payments(limit=15)
    if not pays:
        await cb.message.edit_text(
            "✅ Kutilayotgan to'lov yo'q.",
            reply_markup=admin_back_kb().as_markup(),
        )
        await cb.answer()
        return
    lines = [f"🧾 <b>Kutilayotgan to'lovlar ({len(pays)}):</b>\n"]
    for p in pays:
        name = (p.get("full_name") or p.get("username") or "-")[:20]
        lines.append(
            f"#{p['id']} · {esc(str(name))} · ${p['amount_usd']} · "
            f"<code>{p['user_id']}</code>"
        )
    lines.append("\nTafsilot va tasdiqlash uchun bosing 👇")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=pending_payments_kb(pays).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:vipinfo:"))
async def cb_vip_info(cb: CallbackQuery):
    pid = int(cb.data.rsplit(":", 1)[-1])
    p = await db.get_payment(pid)
    if not p:
        await cb.answer("⚠️ Topilmadi.", show_alert=True)
        return
    from utils.keyboards import admin_payment_kb

    status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌", "paid": "⭐️"}.get(
        p["status"], "•"
    )
    text = _payment_line(p) + f"\n\nHolat: {status_icon} <b>{p['status']}</b>"
    markup = (
        admin_payment_kb(pid).as_markup()
        if p["status"] == "pending"
        else admin_back_kb().as_markup()
    )
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.message(Command("payments"))
async def cmd_payments(message: Message):
    from utils.keyboards import pending_payments_kb

    pays = await db.pending_payments(limit=15)
    if not pays:
        await message.answer("✅ Kutilayotgan to'lov yo'q.")
        return
    lines = [f"🧾 <b>Kutilayotgan to'lovlar ({len(pays)}):</b>\n"]
    for p in pays:
        lines.append(f"{_payment_line(p)}\n")
    await message.answer(
        "\n".join(lines),
        reply_markup=pending_payments_kb(pays).as_markup(),
    )


@router.callback_query(F.data.startswith("adm:userinfo:"))
async def cb_userinfo(cb: CallbackQuery):
    uid = int(cb.data.rsplit(":", 1)[-1])
    u = await db.get_user(uid)
    if not u:
        await cb.answer("⚠️ Foydalanuvchi topilmadi.", show_alert=True)
        return
    vip_until = await db.get_vip_until(uid)
    trial = await db.trial_status(uid)

    uname = f"@{u['username']}" if u.get("username") else "-"
    status = "🚫 bloklangan" if u["is_banned"] else "✅ faol"
    if uid in config.ADMIN_IDS or (vip_until and vip_until > datetime.now(timezone.utc)):
        vip_line = f"💎 VIP: <b>{vip_until.strftime('%d.%m.%Y') if vip_until else '∞'}</b>"
    elif trial and trial["active"]:
        vip_line = f"🎁 Sinov: <b>{trial['days_left']} kun qoldi</b>"
    else:
        vip_line = "💎 VIP: yo'q"

    text = (
        f"👤 <b>Foydalanuvchi</b>\n\n"
        f"🆔 <code>{uid}</code>\n"
        f"👤 {esc(u.get('full_name') or '-')} · {uname}\n"
        f"📅 Qo'shildi: {str(u.get('joined_at'))[:16].replace('T', ' ')}\n"
        f"🔢 So'rovlar: {u.get('requests', 0)}\n"
        f"🌐 Til: {u.get('language') or '-'}\n"
        f"Holat: {status}\n{vip_line}"
    )
    await cb.message.edit_text(text, reply_markup=user_detail_kb(u).as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("adm:vipgrant:"))
async def cb_vip_grant(cb: CallbackQuery):
    _, _, uid_raw, days_raw = cb.data.split(":")
    uid, days = int(uid_raw), int(days_raw)
    until = await db.set_vip(uid, days, "admin_panel")
    await cb.message.edit_reply_markup(
        reply_markup=user_detail_kb(await db.get_user(uid)).as_markup()
    )
    try:
        lang = await get_lang(uid)
        await cb.bot.send_message(
            uid,
            t(
                lang,
                "vip_activated",
                label=f"{days} kunlik VIP",
                until=until[:16].replace("T", " "),
            ),
        )
    except Exception:
        log.warning("vipgrant notify failed for %s", uid)
    await cb.answer(f"✅ +{days} kun VIP berildi", show_alert=True)


@router.callback_query(F.data.startswith("adm:viprevoke:"))
async def cb_vip_revoke(cb: CallbackQuery):
    uid = int(cb.data.rsplit(":", 1)[-1])
    ok = await db.revoke_vip(uid)
    with contextlib.suppress(Exception):
        u = await db.get_user(uid)
        if u:
            await cb.message.edit_reply_markup(
                reply_markup=user_detail_kb(u).as_markup()
            )
    await cb.answer(
        "✅ VIP olib tashlandi" if ok else "⚠️ VIP topilmadi",
        show_alert=True,
    )


@router.callback_query(F.data == "adm:vips")
async def cb_vips(cb: CallbackQuery):
    from utils.keyboards import vips_list_kb

    vips = await db.list_active_vips(limit=20)
    if not vips:
        await cb.message.edit_text(
            "💎 Faol VIP obunachi yo'q.",
            reply_markup=admin_back_kb().as_markup(),
        )
        await cb.answer()
        return
    lines = [f"💎 <b>VIP obunachilar ({len(vips)}):</b>\n"]
    for v in vips:
        name = v.get("username") or v.get("full_name") or str(v["user_id"])
        lines.append(f"• {esc(str(name)[:22])} · {v['days_left']} kun · <code>{v['user_id']}</code>")
    lines.append("\nBoshqarish uchun bosing 👇 (kartada olib tashlash tugmasi bor)")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=vips_list_kb(vips).as_markup()
    )
    await cb.answer()


@router.callback_query(F.data == "adm:scan")
async def cb_scan(cb: CallbackQuery):
    from scheduler import run_scan_cycle

    await cb.answer("⚡️ Skanerlash boshlandi...")
    status = await cb.message.answer("⚡️ Qo'lda skanerlash ishga tushdi...")
    try:
        count = await run_scan_cycle(cb.bot)
        await status.edit_text(f"✅ Skaner tugadi. Yuborilgan xabarlar: <b>{count}</b>")
    except Exception:
        log.exception("panel scan failed")
        await status.edit_text("❌ Skanerda xatolik. Loglarni tekshiring.")


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
