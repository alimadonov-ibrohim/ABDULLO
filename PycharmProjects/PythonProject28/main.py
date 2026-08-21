import asyncio
import os
import shutil
import time
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon import TelegramClient, errors, functions, types as tg_types

# Kod @MamurZokirov tomonidan tuzib chiqilgan

# Manba @MamurZokirov & @lock_pro


def load_env(path=".env"):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


load_env()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_FOLDER = ".sesiya"

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise SystemExit("❌ API_ID / API_HASH / BOT_TOKEN topilmadi! .env faylni to'ldiring.")

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class LoginStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_2fa = State()


clients = []
user_sessions = {}
current_idx = 0


async def init_clients():
    """Papkadagi barcha sessiyalarni yuklash"""
    global clients

    for c in clients:
        try:
            await c.disconnect()
        except:
            pass

    clients = []
    if not os.path.exists(SESSION_FOLDER): return

    files = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session')]
    for file in files:
        session_path = os.path.join(SESSION_FOLDER, file)
        client = TelegramClient(session_path, API_ID, API_HASH)
        try:
            await client.connect()
            if await client.is_user_authorized():
                clients.append(client)
            else:
                await client.disconnect()
        except Exception as e:
            print(f"Sessiya yuklashda xato ({file}): {e}")
    print(f"✅ {len(clients)} ta akkaunt tayyor!")


@dp.message_handler(commands=['sms'], state="*")
async def cmd_sms(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    files = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session')]

    if files:
        for file in files:
            phone_num = file.replace(".session", "")
            keyboard.add(types.InlineKeyboardButton(
                text=f"📞 {phone_num} (O'chirish❌)",
                callback_data=f"del_acc:{phone_num}"
            ))

    keyboard.add(types.InlineKeyboardButton(text="➕ Yangi akkaunt ulash", callback_data="add_new_account"))

    await message.answer(
        "👥 <b>Ulangan akkauntlar boshqaruvi:</b>\n\n<i>Akkauntni o'chirish uchun ustiga bosing yoki yangi raqam qo'shing:</i>",
        reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data == "add_new_account", state="*")
async def handle_add_new_acc(call: types.CallbackQuery):
    await call.message.edit_text("📞 Raqamni kiriting (masalan: +998901234567):")
    await LoginStates.waiting_for_phone.set()


@dp.callback_query_handler(lambda call: call.data.startswith("del_acc:"), state="*")
async def handle_del_acc(call: types.CallbackQuery):
    phone_to_del = call.data.split(":")[1]
    session_file = os.path.join(SESSION_FOLDER, f"{phone_to_del}.session")
    session_journal = os.path.join(SESSION_FOLDER, f"{phone_to_del}.session-journal")

    global clients
    for c in clients:
        try:
            me = await c.get_me()
            if me and me.phone and phone_to_del in me.phone:
                await c.disconnect()
                clients.remove(c)
                break
        except:
            pass

    try:
        if os.path.exists(session_file): os.remove(session_file)
        if os.path.exists(session_journal): os.remove(session_journal)
        await call.answer(f"✅ {phone_to_del} tizimdan to'liq o'chirildi!", show_alert=True)
    except Exception as e:
        await call.answer(f"Faylni o'chirishda xato: {e}", show_alert=True)

    await init_clients()
    await call.message.delete()


@dp.message_handler(state=LoginStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip().replace(" ", "")
    session_path = os.path.join(SESSION_FOLDER, f"{phone}.session")
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()

    try:
        code_hash = await client.send_code_request(phone)
        user_sessions[message.from_user.id] = {'client': client, 'phone': phone, 'code_hash': code_hash.phone_code_hash}
        await message.answer("📩 Kodni kiriting (nuqtalar bilan bo'lsa ham: 1.2.3.4.5):")
        await LoginStates.waiting_for_code.set()
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
        await client.disconnect()
        await state.finish()


@dp.message_handler(state=LoginStates.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    data = user_sessions.get(message.from_user.id)
    if not data:
        await message.answer("Sessiya topilmadi, qaytadan /sms yozing.")
        await state.finish()
        return

    code = message.text.replace(".", "").strip()
    client = data['client']

    try:
        await client.sign_in(data['phone'], code, phone_code_hash=data['code_hash'])
        await message.answer("✅ Akkaunt muvaffaqiyatli ulandi!")
        await client.disconnect()
        await init_clients()
        await state.finish()
    except errors.SessionPasswordNeededError:
        await message.answer("🔐 2FA parol yozing:")
        await LoginStates.waiting_for_2fa.set()
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
        await client.disconnect()
        await state.finish()


@dp.message_handler(state=LoginStates.waiting_for_2fa)
async def process_2fa(message: types.Message, state: FSMContext):
    data = user_sessions.get(message.from_user.id)
    if not data:
        await state.finish()
        return

    client = data['client']
    try:
        await client.sign_in(password=message.text.strip())
        await message.answer("✅ 2FA orqali ulandi!")
        await client.disconnect()
        await init_clients()
        await state.finish()
    except Exception as e:
        await message.answer(f"❌ Parol xatosi: {e}")
        await client.disconnect()
        await state.finish()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    text = (
        f"Salom {message.from_user.first_name}, xush kelibsiz!\n\n"
        "<b>Quyidagi qo'llanmadan foydalaning:</b>\n"
        "📊 /stats - Statistika va Targetlar tahlili\n"
        "🎯 /target [guruh_user] - Kanal/guruh ulab admin qilish\n"
        "📞 /sms - Akkauntlarni boshqarish (Tugmalar ro'yxati)\n"
        "⚙️ /info [guruh_user] - Tezkor tahlil\n"
        "🚪 /end - Seansni yakunlash\n\n"
        "<i>/[guruh_user] - Tozalashni boshlash uchun</i>"
    )
    await message.answer(text)


async def promote_others(target_chat):
    if not clients:
        print("❌ Tizimda faol akkauntlar topilmadi!")
        return False, "Tizimda faol akkauntlar yo'q!"

    admin_client = None
    chat_entity = None

    print(f"🔎 @{target_chat} guruhida adminlik huquqi bor akkaunt qidirilmoqda...")
    for client in clients:
        try:

            entity = await client.get_entity(target_chat)
            permissions = await client.get_permissions(entity, 'me')

            if permissions.is_admin and (permissions.is_creator or permissions.add_admins):
                admin_client = client
                chat_entity = entity
                me = await client.get_me()
                print(f"👑 admin akkaunt: +{me.phone}")
                break
        except Exception:
            continue

    if not admin_client:
        print("❌ Guruhda boshqalarni admin qila oladigan birorta ham akkaunt topilmadi!")
        return False, "Siz ulagan akkauntlar ichida bu guruhning 'Yaratuvchisi' yoki 'Admin qo'shish' huquqi bor admin topilmadi!"

    promoted_count = 0
    for client in clients:
        if client == admin_client:
            continue

        try:
            other_user = await client.get_me()

            try:

                await client(functions.channels.JoinChannelRequest(channel=chat_entity))
                print(f"✅ +{other_user.phone} guruhga avtomatik obuna bo'ldi.")
            except Exception as e:

                try:
                    await admin_client(functions.channels.InviteToChannelRequest(
                        channel=chat_entity, users=[other_user.id]
                    ))
                    print(f"📩 +{other_user.phone} admin akkaunt tomonidan taklif qilindi.")
                except Exception as inv_err:
                    print(f"⚠️ +{other_user.phone} guruhga kira olmadi: {inv_err}")
                    continue
            await admin_client(functions.channels.EditAdminRequest(
                channel=chat_entity,
                user_id=other_user.id,
                admin_rights=tg_types.ChatAdminRights(
                    ban_users=True,
                    invite_users=True,
                    delete_messages=True,
                    pin_messages=True
                ),
                rank="Helper"
            ))
            print(f"🛰 Akkaunt +{other_user.phone} muvaffaqiyatli admin qilindi!")
            promoted_count += 1

        except Exception as e:
            print(f"⚠️ Akkauntni admin qilishda xatolik: {e}")

    return True, f"Muvaffaqiyatli! {promoted_count} ta akkaunt avtomatik guruhga a'zo bo'lib, adminlik huquqini oldi."


@dp.message_handler(commands=['target'])
async def cmd_target(message: types.Message):
    target = message.get_args().replace("@", "").strip()
    if not target:
        return await message.answer("❌ Xato! /target guruh_user ko'rinishida yozing.")

    await message.answer(f"🎯 <b>@{target}</b> tizimda tahlil qilinmoqda, akkauntlar huquqlari tekshirilmoqda...")

    success, status_text = await promote_others(target)

    if success:

        with open("target.txt", "a") as f:
            f.write(f"{target}\n")
        await message.answer(f"✅ <b>{status_text}</b>\nTarget muvaffaqiyatli <code>target.txt</code> fayliga saqlandi!")

    else:
        await message.answer(f"❌ <b>Muvaffaqiyatsiz!</b>\n{status_text}")


@dp.message_handler(commands=['info'])
async def cmd_info(message: types.Message):
    username = message.get_args().replace("@", "").strip()
    if not username:
        return await message.answer("Target foydalanuvchi nomini yozing. (Masalan: /info guruh_user)")
    if not clients:
        return await message.answer("❌ Tizimda faol akkauntlar mavjud emas!")

    await message.answer(
        "🔎 <b>Guruh chuqur skanerlanmoqda...</b>\n<i>(Katta guruhlarda biroz vaqt olishi mumkin, kuting)</i>")

    search_queries = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    ]

    unique_users = set()
    prem_m = 0

    try:
        client = clients[0]

        full_chat = await client(functions.channels.GetFullChannelRequest(channel=username))
        real_total_count = full_chat.full_chat.participants_count

        for query in search_queries:
            try:

                async for user in client.iter_participants(username, search=query):
                    if user.bot: continue

                    if user.id not in unique_users:
                        unique_users.add(user.id)
                        if user.premium:
                            prem_m += 1
            except Exception as e:
                print(f"Harf skanerlashda xato ({query}): {e}")
                continue

            await asyncio.sleep(0.2)

        total_found = len(unique_users)
        oddiy_m = total_found - prem_m

        if real_total_count > total_found and total_found > 0:
            ratio = prem_m / total_found
            final_premium = int(real_total_count * ratio)
            final_oddiy = real_total_count - final_premium
        else:
            final_premium = prem_m
            final_oddiy = real_total_count - prem_m

        text = (
            f"📊 <b>Guruh: @{username}</b>\n"
            f"📊 <b>Haqiqiy Jami a'zo:</b> {real_total_count} ta\n"
            f"🔍 <b>Chuqur skanerda topilganlar:</b> {total_found} ta\n"
            f"💎 <b>Aniq Premium a'zo:</b> {final_premium} ta\n"
            f"👤 <b>Aniq Oddiy a'zo:</b> {final_oddiy} ta\n\n"
        )
        await message.answer(text)

    except errors.ChatAdminRequiredError:
        await message.answer(
            f"❌ <b>Xatolik:</b> Siz @{username} guruhida admin emassiz yoki a'zolar ro'yxati yashirilgan!")
    except Exception as e:
        await message.answer(f"❌ Kutilmagan xato: {e}")


@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    if not os.path.exists("target.txt"):
        return await message.answer("❌ Hozircha hech qanday target guruh qo'shilmagan!")

    with open("target.txt", "r") as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]

    if not targets:
        return await message.answer("❌ Targetlar ro'yxati bo'sh!")

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    full_report = "📝 <b>Joriy Target Guruhlar Ro'yxati:</b>\n\n"

    for idx, target in enumerate(targets, start=1):
        full_report += f"{idx}. 🎯 @{target}\n"
        keyboard.add(types.InlineKeyboardButton(
            text=f"❌ @{target} ni o'chirish",
            callback_data=f"del_target:{target}"
        ))

    full_report += "\n<i>💡 Guruh a'zolarini bilish uchun: <code>/info [guruh_user]</code></i>"
    await message.answer(full_report, reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('del_target:'))
async def handle_delete_target(call: types.CallbackQuery):
    target_to_del = call.data.split(":")[1]
    if not os.path.exists("target.txt"):
        return await call.answer("❌ Fayl topilmadi!", show_alert=True)

    with open("target.txt", "r") as f:
        lines = f.readlines()

    remaining_targets = [line.strip() for line in lines if line.strip() != target_to_del and line.strip()]

    with open("target.txt", "w") as f:
        for tg in remaining_targets:
            f.write(f"{tg}\n")

    await call.answer(f"✅ @{target_to_del} o'chirildi!", show_alert=True)

    try:
        await call.message.delete()
    except Exception:
        pass

    if not remaining_targets:
        await call.message.answer("❌ Hozircha hech qanday target guruh qo'shilmagan!")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    full_report = "📝 <b>Joriy Target Guruhlar Ro'yxati:</b>\n\n"

    for idx, target in enumerate(remaining_targets, start=1):
        full_report += f"{idx}. 🎯 @{target}\n"
        keyboard.add(types.InlineKeyboardButton(
            text=f"❌ @{target} ni o'chirish",
            callback_data=f"del_target:{target}"
        ))

    full_report += "\n<i>💡 Guruh a'zolarini bilish uchun: <code>/info [guruh_user]</code></i>"

    await call.message.answer(full_report, reply_markup=keyboard)


async def send_admin_log(message_obj: types.Message, text: str):
    """Xatolik va jarayonlarni buyruq bergan adminga jonli yuborish"""
    try:

        await message_obj.bot.send_message(
            chat_id=message_obj.chat.id,
            text=f"📝 <b>LOG:</b> {text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Log yuborishda xato: {e}")


flood_expiry = {}


@dp.message_handler(lambda message: message.text.startswith('/'))
async def kick_logic(message: types.Message):
    target = message.text[1:].replace("@", "").strip()
    if target in ['start', 'stats', 'target', 'list', 'info', 'end', 'sms']: return
    if not clients: return await message.answer("❌ Tizimda faol akkauntlar yo'q!")

    await message.answer(f"🚀 @{target} guruhini chuqur tozalash boshlandi. Jarayon loglari shu yerga yuboriladi...")

    global current_idx
    kicked = 0

    search_queries = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    ]

    processed_users = set()

    try:
        for query in search_queries:
            current_time = time.time()

            scanner_client = None
            for client in clients:
                if flood_expiry.get(id(client), 0) < current_time:
                    scanner_client = client
                    break

            if not scanner_client:
                await send_admin_log(message, "⏳ Hamma akkauntlar floodda! 15 soniya tanaffus...")
                await asyncio.sleep(15)
                scanner_client = clients[0]

            try:
                async for user in scanner_client.iter_participants(target, search=query):
                    if user.bot or user.premium: continue
                    if user.id in processed_users: continue

                    processed_users.add(user.id)

                    while True:
                        current_time = time.time()
                        available_clients = [c for c in clients if flood_expiry.get(id(c), 0) < current_time]

                        if not available_clients:
                            next_expiry = min(flood_expiry.values())
                            wait_time = int(next_expiry - current_time) + 1
                            if wait_time <= 0: wait_time = 5
                            await send_admin_log(message,
                                                 f"⏳ Barcha akkauntlar cheklovda. Birinchisi chiqguncha {wait_time}s kutilmoqda...")
                            await asyncio.sleep(wait_time)
                            continue

                        old_idx = current_idx

                        if current_idx >= len(clients) or clients[current_idx] not in available_clients:
                            current_idx = clients.index(available_clients[0])

                        active_client = clients[current_idx]

                        if old_idx != current_idx:
                            try:
                                old_me = await clients[old_idx].get_me()
                                new_me = await active_client.get_me()
                                old_phone = f"+{old_me.phone}" if old_me.phone else f"Acc #{old_idx + 1}"
                                new_phone = f"+{new_me.phone}" if new_me.phone else f"Acc #{current_idx + 1}"
                                await send_admin_log(message,
                                                     f"🛰 <b>Akkaunt almashdi:</b> <code>{old_phone}</code> ➡️ <code>{new_phone}</code>")
                            except:
                                await send_admin_log(message,
                                                     f"🛰 <b>Akkaunt almashdi:</b> #{old_idx + 1}-akkaunt ➡️ #{current_idx + 1}-akkauntga o'tdi.")

                        try:

                            await active_client.kick_participant(target, user.id)
                            kicked += 1
                            current_idx = (current_idx + 1) % len(clients)
                            break

                        except errors.FloodWaitError as e:
                            flood_expiry[id(active_client)] = time.time() + e.seconds

                            try:
                                me = await active_client.get_me()
                            except:
                                me = None
                            acc_name = f"+{me.phone}" if (me and me.phone) else f"Acc #{current_idx + 1}"

                            await send_admin_log(message,
                                                 f"⚠️ <b>{acc_name}</b> floodga tushdi! Telegram {e.seconds} soniya jazo berdi va vaqtincha chetlatildi.")

                            current_idx = (current_idx + 1) % len(clients)
                            continue

                        except errors.rpcerrorlist.UserIdInvalidError:

                            await send_admin_log(message,
                                                 f"ℹ️ Foydalanuvchi (ID: {user.id}) guruhda topilmadi, o'tkazib yuborildi.")
                            break

                        except errors.ChatAdminRequiredError:
                            return await message.answer("❌ Xatolik: Akkauntda guruhdan odam haydash huquqi yo'q!")
                        except Exception as e:

                            await send_admin_log(message, f"⚠️ Kick bajarilmadi (User ID: {user.id}): {e}")
                            break

                    await asyncio.sleep(0.3)

            except Exception as search_err:
                print(f"⚠️ '{query}' harfi bo'yicha qidiruvda xato: {search_err}")
                continue

    except errors.ChatAdminRequiredError:
        return await message.answer(f"❌ @{target} guruhida skanerlash uchun admin huquqi yetarli emas.")
    except Exception as e:
        return await message.answer(f"❌ Kutilmagan xatolik: {e}")

    await message.answer(f"🏁 Jami: {kicked} ta haqiqiy oddiy a'zo guruhdan muvaffaqiyatli chiqarib yuborildi 🚀")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_clients())
    executor.start_polling(dp, skip_updates=True)