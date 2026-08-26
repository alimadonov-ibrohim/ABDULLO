import time

import config
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from database import db
from logger import get_logger
from utils.formatters import esc
from utils.i18n import get_lang, t
from utils.keyboards import back_to_main, paid_confirm_kb, vip_menu

log = get_logger("handlers.vip")

router = Router(name="vip")

# Chek kutayotgan foydalanuvchilar: {user_id: (payment_id, started_at)}
_await_receipt: dict[int, tuple[int, float]] = {}
_RECEIPT_TTL_SEC = 600


# ---------------- yordamchi ----------------

def _receipt_filter(m: Message) -> bool:
    u = getattr(m, "from_user", None)
    if not u:
        return False
    item = _await_receipt.get(u.id)
    if not item or time.monotonic() - item[1] > _RECEIPT_TTL_SEC:
        return False
    txt = (getattr(m, "text", "") or "")
    return not txt.startswith("/")


async def _notify_admins_new_order(bot, payment: dict) -> None:
    """Adminlarga yangi buyurtma haqida xabar."""
    uname = f"@{payment['username']}" if payment.get("username") else "-"
    plan = config.VIP_PLANS.get(payment["plan"], {})
    label = plan.get("label", payment["plan"])
    text = (
        f"🧾 <b>Yangi buyurtma #{payment['id']}</b>\n\n"
        f"👤 {esc(payment['full_name'] or '-')} · {uname}\n"
        f"🆔 <code>{payment['user_id']}</code>\n"
        f"💎 {esc(label)} — ${payment['amount_usd']}\n"
        f"⏳ Chek kutilmoqda..."
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            log.warning("admin notify failed for %s", admin_id)


async def activate_vip_and_notify(
    bot, user_id: int, plan_key: str, method: str
) -> str:
    """VIP'ni faollashtiradi va foydalanuvchini tabriklaydi. until qaytaradi."""
    plan = config.VIP_PLANS[plan_key]
    until = await db.set_vip(user_id, plan["days"], f"{method}:{plan_key}")
    lang = await get_lang(user_id)
    try:
        await bot.send_message(
            user_id,
            t(
                lang,
                "vip_activated",
                label=esc(plan["label"]),
                until=until[:16].replace("T", " "),
            ),
        )
    except Exception:
        log.warning("vip activation notify failed for %s", user_id)
    return until


# ---------------- VIP menyusi ----------------

def _admin_contact_button(lang: str) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=t(lang, "vip_pay_admin_btn"),
            url=f"https://t.me/{config.PAYMENT_CONTACT.lstrip('@')}",
        )
    ]


async def vip_info_content(
    user_id: int, lang: str = "uz"
) -> tuple[str, object]:
    is_vip = await db.is_vip(user_id)
    until = await db.get_vip_until(user_id)

    unlimited = t(lang, "vip_unlimited_admin")
    if is_vip:
        until_txt = until.strftime("%d.%m.%Y %H:%M UTC") if until else unlimited
        status = t(lang, "vip_active", until=until_txt)
    else:
        status = t(lang, "vip_not_active")

    plans_lines = [t(lang, "vip_plans_title")]
    for key, plan in config.VIP_PLANS.items():
        plans_lines.append(
            f"• {plan['label']}: <b>${plan['price_usd']}</b> "
            f"<i>({plan['description']})</i>"
        )

    text = t(lang, "vip_title") + "\n\n" + status + "\n".join(plans_lines) + t(
        lang, "vip_benefits"
    )
    return text, vip_menu(lang, is_vip).as_markup()


@router.callback_query(F.data == "menu:vip")
async def show_vip_info_cb(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    text, markup = await vip_info_content(cb.from_user.id, lang)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.message(Command("vip"))
async def cmd_vip(message: Message):
    lang = await get_lang(message.from_user.id)
    text, markup = await vip_info_content(message.from_user.id, lang)
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "vip:status")
async def cb_vip_status(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    is_vip = await db.is_vip(cb.from_user.id)
    until = await db.get_vip_until(cb.from_user.id)
    unlimited = t(lang, "vip_unlimited_admin")
    if is_vip:
        until_txt = (
            until.strftime("%d.%m.%Y %H:%M") if until else unlimited
        )
        text = t(lang, "vip_status_ok", until=until_txt)
    else:
        text = t(lang, "vip_status_no")
    extra = (
        [
            InlineKeyboardButton(
                text=t(lang, "vip_plans_btn"), callback_data="menu:vip"
            )
        ]
        if not is_vip
        else None
    )
    await cb.message.edit_text(text, reply_markup=back_to_main(lang, extra).as_markup())
    await cb.answer()


# ---------------- Reja -> to'lov ko'rsatmalari ----------------

@router.callback_query(F.data.startswith("vip:plan:"))
async def cb_vip_plan(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    key = cb.data.split(":")[-1]
    plan = config.VIP_PLANS.get(key)
    if not plan:
        await cb.answer(t(lang, "plan_not_found"), show_alert=True)
        return

    lines = [
        t(lang, "pay_manual_title", label=esc(plan["label"]), price=plan["price_usd"])
    ]
    if config.PAYMENT_CARD:
        lines.append(f"\n💳 Karta: <code>{config.PAYMENT_CARD}</code>")
    if config.PAYMENT_CRYPTO:
        lines.append(f"🪙 Crypto: <code>{config.PAYMENT_CRYPTO}</code>")
    lines.append("\n" + t(lang, "pay_manual_contact", contact=config.PAYMENT_CONTACT))

    await cb.message.edit_text(
        "\n".join(lines), reply_markup=paid_confirm_kb(key, lang).as_markup()
    )
    await cb.answer()


# ---------------- Buyurtma + chek ----------------

@router.callback_query(F.data.startswith("vip:paid:"))
async def cb_vip_paid(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    key = cb.data.split(":")[-1]
    plan = config.VIP_PLANS.get(key)
    if not plan:
        await cb.answer(t(lang, "plan_not_found"), show_alert=True)
        return

    # bir xil pending buyurtmani takrorlamaslik
    for p in await db.pending_payments(limit=50):
        if p["user_id"] == cb.from_user.id and p["plan"] == key:
            await cb.answer(t(lang, "pay_already_pending"), show_alert=True)
            return

    pid = await db.create_payment(
        user_id=cb.from_user.id,
        username=cb.from_user.username,
        full_name=cb.from_user.full_name,
        plan=key,
        amount_usd=plan["price_usd"],
        method="manual",
    )
    _await_receipt[cb.from_user.id] = (pid, time.monotonic())
    await cb.message.edit_text(t(lang, "pay_send_receipt"))
    await _notify_admins_new_order(cb.bot, dict(await db.get_payment(pid)))
    await cb.answer()


@router.message(_receipt_filter, F.photo | F.document | F.text)
async def receive_receipt(message: Message):
    uid = message.from_user.id
    item = _await_receipt.pop(uid, None)
    pid = item[0] if item else None
    if not pid:
        return
    p = await db.get_payment(pid)
    if not p or p["status"] != "pending":
        return

    lang = await get_lang(uid)
    name = p["full_name"] or "-"
    uname = f"@{p['username']}" if p.get("username") else "-"

    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🧾 <b>Chek keldi — buyurtma #{pid}</b>\n"
                f"👤 {esc(str(name))} · {uname} · 🆔 <code>{uid}</code>\n"
                f"💎 {esc(p['plan'])} — ${p['amount_usd']}",
                reply_markup=(await _admin_kb_if_pending(pid)),
            )
            await message.copy_to(admin_id)
        except Exception:
            log.exception("receipt forward failed for admin %s", admin_id)

    await db.set_payment_payload(pid, "receipt_received")
    await message.answer(t(lang, "pay_receipt_thanks"))


async def _admin_kb_if_pending(pid: int):
    from utils.keyboards import admin_payment_kb

    p = await db.get_payment(pid)
    if p and p["status"] == "pending":
        return admin_payment_kb(pid).as_markup()
    return None


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    u = message.from_user
    uname = f"\n👤 @{u.username}" if u.username else ""
    await message.answer(f"🆔 Sizning ID: <code>{u.id}</code>{uname}")
