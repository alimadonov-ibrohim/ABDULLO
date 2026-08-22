import config
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from database import db
from logger import get_logger
from utils.formatters import esc
from utils.i18n import get_lang, t
from utils.keyboards import back_to_main, vip_menu

log = get_logger("handlers.vip")

router = Router(name="vip")


def _admin_contact_button(lang: str) -> list[InlineKeyboardButton]:
    if config.ADMIN_IDS:
        return [
            InlineKeyboardButton(
                text=t(lang, "vip_pay_admin_btn"),
                url=f"tg://user?id={config.ADMIN_IDS[0]}",
            )
        ]
    return []


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


@router.callback_query(F.data.startswith("vip:plan:"))
async def cb_vip_plan(cb: CallbackQuery):
    lang = await get_lang(cb.from_user.id)
    key = cb.data.split(":")[-1]
    plan = config.VIP_PLANS.get(key)
    if not plan:
        await cb.answer(t(lang, "plan_not_found"), show_alert=True)
        return

    title = t(lang, "vip_title").replace("💎 <b>", "").replace("</b>", "")
    text = (
        f"💎 <b>{esc(plan['label'])} — ${plan['price_usd']}</b>\n"
        f"<i>{esc(plan['description'])}</i>\n\n"
        + t(lang, "vip_plan_details", uid=cb.from_user.id)
    )
    kb = back_to_main(lang, _admin_contact_button(lang))
    await cb.message.edit_text(text, reply_markup=kb.as_markup())
    await cb.answer()
