import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from cards import make_card

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8812859354:AAGD8J4VTucwkhHMsQWczfU5WZqjz70o-Ik"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CATEGORIES = {
    "bolalar": {
        "emoji": "🧒",
        "title": "Bolalar",
        "greetings": [
            "Sevimli {name}jon, tug'ilgan kuning muborak bo'lsin! 🎂\n\n"
            "Bugun sen bilan birga quvonamiz, o'sishingni, o'qishingni va har kuni yanada aqlli bo'lib borishingni tilaymiz! 🌟\n\n"
            "Barcha orzularing amalga oshsin, doim shod va baxtli bo'l! 🎈🎁",
            "Qadrli {name}jon! 🎉\n\n"
            "Tug'ilgan kuning bilan! Bugun butun dunyo sen uchun! 🌍\n\n"
            "Bola bo'lib o'ynang, quvong, kuling — hayoting shirin konfetday shirin bo'lsin! 🍬🎠",
            "Assalomu alaykum, aziz {name}! 🎊\n\n"
            "Tug'ilgan kuning muborak! Senga eng yorqin o'yinchoqlar, eng mazali tortlar va do'stlaring bilan quvnoq kunlar tilaymiz! 🎂🧸\n\n"
            "Ota-onangni doim hurmat qil, ulg'ayib borishga shoshma — bolalik quvonchlaridan zavqlan! 🥳",
        ],
    },
    "qizlar": {
        "emoji": "👧",
        "title": "Qizlar",
        "greetings": [
            "Go'zal {name}jon, tug'ilgan kuning muborak bo'lsin! 🌸\n\n"
            "Bugun tong senga tabassum bilan, quyosh esa iliq nurlari bilan keldi. Sen shunchalik go'zal va mehribonsan! ✨\n\n"
            "Orzularing gullar kabi ochilsin, ko'ngling doim bahor bo'lsin! 💐🌷",
            "Aziz {name}! 🎀\n\n"
            "Tug'ilgan kuning bilan! Bu yil senga yangi orzular, yangi muvaffaqiyatlar va cheksiz baxt olib kelsin! 🦋\n\n"
            "Doim shunday go'zal, aqlli va o'ziga ishongan bo'lib qol! Yulduzlar ham senga havas qiladi! 🌟",
            "Tabriklaymiz, {name}jon! 🎂💖\n\n"
            "Shu kun dunyoning eng chiroyli qizi — sen tug'ilgan kun! Barcha tilaklaring ushalganday bo'lsin, qalbing quvonchga to'lsin! 💝\n\n"
            "Omading doim yoningda bo'lsin, yuzingdan tabassum arimasin! 🌺",
        ],
    },
    "ayollar": {
        "emoji": "👩",
        "title": "Ayollar",
        "greetings": [
            "Hurmatli {name} opa/xonim, tug'ilgan kuningiz muborak bo'lsin! 🌹\n\n"
            "Sizning mehringiz, sabringiz va mehr-oqibatligingiz uchun minnatdormiz. Oilangizga tinchlik, sog'liq va farovonlik tilaymiz! 🤲\n\n"
            "Kunlaringiz guldek ochilsin, qalbingiz doim iliq bo'lsin! 💐",
            "Qadrli {name}! 🎉\n\n"
            "Tug'ilgan kuningiz bilan! Sizga mustahkam sog'liq, oilaviy baxt, moddiy baraka va cheksiz quvonch tilaymiz! ✨\n\n"
            "Har kuni o'zingizni eng go'zal va baxtli his eting, chunki siz shunga loyiqsiz! 💖",
            "Hurmatli {name}! 🌷\n\n"
            "Tug'ilgan kuningiz muborak! Hayot yo'lingiz gul-u chaman bo'lsin, xonadoningizga xotirjamlik, yurakingizga esa tinchlik joylashsin! 🕊️\n\n"
            "Barcha istaklaringiz amalga oshsin, doim shodlikda yashang! 🥂",
        ],
    },
    "erkaklar": {
        "emoji": "👨",
        "title": "Erkaklar",
        "greetings": [
            "Hurmatli {name} aka, tug'ilgan kuningiz muborak bo'lsin! 🎉\n\n"
            "Sizga mustahkam sog'liq, katta muvaffaqiyatlar, oilangizga farovonlik va baraka tilaymiz! 💪\n\n"
            "Ishingizda va hayotingizda doim g'alaba sizniki bo'lsin! 🏆",
            "Qadrli {name}! 🥂\n\n"
            "Tug'ilgan kuningiz bilan! Omadingiz to'g'ri kelsin, niyatlaringiz qabul bo'lsin, do'stlaringiz sodiq, oilangiz sog' bo'lsin! 🤲\n\n"
            "Har bir kuningiz yangi yutuqlar bilan to'lsin! 🚀",
            "Hurmatli {name} aka! 🌟\n\n"
            "Tug'ilgan kuningiz muborak! Siz kabi jasur, olijanob va mehribon insonlarning yoshini Alloh uzaytirsin! 🕊️\n\n"
            "Rejalaringiz amalga oshsin, yo'lingiz doim oq yorug' bo'lsin! 💫",
        ],
    },
    "bobolar": {
        "emoji": "👴",
        "title": "Bobolar (55+)",
        "greetings": [
            "Muborak yosh, hurmatli bobojon! 👴🎉\n\n"
            "Tug'ilgan kuningiz bilan tabriklaymiz! Oltin asringizda sog'lik mustahkam, ko'nglingiz shod, xonadoningiz farovon bo'lsin! 🕊️\n\n"
            "Farzandlaringiz va nabiralaringiz sizdan faxrlansin. Yuz yil umr ko'ring, duolarimiz siz bilan! 🤲",
            "Aziz buvajonim! 👵🌷\n\n"
            "Tug'ilgan kuningiz muborak! Oilamizning ko'rki, mehribon buvajon, umringiz uzun, sog'ligingiz barqaror bo'lsin! 💐\n\n"
            "Har tongingiz nurli, kuningiz xotirjam bo'lsin. Sizni juda yaxshi ko'ramiz! 💖",
            "Hurmatli {name}! 👴✨\n\n"
            "Tug'ilgan kuningiz muborak bo'lsin! Hayot tajribangiz, duoingiz va mehringiz biz uchun eng katta boylik! 🏆\n\n"
            "Alloh sizga uzoq umr, sihat-salomatlik va xotirjam keksalik nasib etsin! 🤲",
        ],
    },
}

WELCOME_TEXT = (
    "🎂 <b>Tug'ilgan kun tabrik botiga xush kelibsiz!</b>\n\n"
    "Bu bot orqali siz o'z yaqinlaringiz uchun chiroyli va samimiy tabriklar yaratishingiz mumkin.\n\n"
    "👇 <b>Quyidagilardan birini tanlang:</b>"
)

NAME_PROMPT = (
    "📝 <b>Tabriklamoqchi bo'lgan insoningizning ismini yozing:</b>\n\n"
    "Misol uchun: <i>Aziza</i> yoki <i>Aziz aka</i>"
)

BACK_BUTTONS = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Yana tabrik", callback_data="regenerate"),
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"),
        ]
    ]
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🎂 Tabrik yaratish")], [KeyboardButton(text="ℹ️ Bot haqida")]],
    resize_keyboard=True,
)


class Form(StatesGroup):
    waiting_name = State()


def category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f"{data['emoji']} {data['title']}",
            callback_data=f"cat:{key}",
        )
        for key, data in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons[:2],
            buttons[2:4],
            [buttons[4]],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=MAIN_KEYBOARD,
    )
    await message.answer("🏠 <b>Bosh menyu</b>", reply_markup=category_keyboard())


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "🎂 Bu bot tug'ilgan kun tabriklarini yaratish uchun mo'ljallangan.\n\n"
        "👧 <b>Qizlar uchun</b> – go'zal va nozik tabriklar\n"
        "👩 <b>Ayollar uchun</b> – samimiy va iliq tabriklar\n"
        "👨 <b>Erkaklar uchun</b> – hurmat va muvaffaqiyat tilaklari\n"
        "🧒 <b>Bolalar uchun</b> – quvnoq va o'ynoqi tabriklar\n"
        "👴 <b>Bobolar (55+)</b> – hurmatli yoshdagi tabriklar\n\n"
        "Foydalanish: <i>Tabrik yaratish</i> tugmasini bosing, kategoriyani tanlang va ism yozing. Hammasi shu! ✨"
    )


@dp.message(F.text == "🎂 Tabrik yaratish")
async def create_button(message: Message):
    await message.answer(WELCOME_TEXT)
    await message.answer("🏠 <b>Bosh menyu</b>", reply_markup=category_keyboard())


@dp.message(F.text == "ℹ️ Bot haqida")
async def about_button(message: Message):
    await help_handler(message)


@dp.callback_query(F.data == "home")
async def home_callback(callback, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 <b>Bosh menyu</b>", reply_markup=category_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "regenerate")
async def regenerate_callback(callback, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    name = data.get("name")
    if category and name:
        greeting = random.choice(CATEGORIES[category]["greetings"]).format(name=name)
        await callback.message.delete()
        await send_birthday_card(callback.message, category, name, greeting)
    await callback.answer()


@dp.callback_query(F.data.startswith("cat:"))
async def category_callback(callback, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    await state.update_data(category=key)
    await callback.message.edit_text(
        f"Tanlangan: {CATEGORIES[key]['emoji']} <b>{CATEGORIES[key]['title']}</b> ✅\n\n{NAME_PROMPT}"
    )
    await state.set_state(Form.waiting_name)
    await callback.answer()


@dp.message(Form.waiting_name, F.text)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) > 40:
        await message.answer("❌ Ism juda uzun. Qisqaroq ism yozing (40 ta belgidan kam):")
        return

    data = await state.get_data()
    category = data.get("category", "erkaklar")
    cat = CATEGORIES[category]
    greeting = random.choice(cat["greetings"]).format(name=name)

    await state.update_data(name=name)
    await send_birthday_card(message, category, name, greeting)
    await state.clear()


async def send_birthday_card(message: Message, category: str, name: str, greeting: str):
    try:
        card_path = make_card(category, name)
        with open(card_path, "rb") as f:
            photo = BufferedInputFile(f.read(), filename="birthday_card.png")
        await message.answer_photo(
            photo,
            caption=f"{CATEGORIES[category]['emoji']} <b>{name}</b>\n\n{greeting}",
            reply_markup=BACK_BUTTONS,
        )
    except Exception as e:
        logging.error(f"Karta yaratishda xatolik: {e}")
        await message.answer(
            f"{CATEGORIES[category]['emoji']} <b>{name}</b>\n\n{greeting}",
            reply_markup=BACK_BUTTONS,
        )


@dp.message(Form.waiting_name)
async def get_name_invalid(message: Message):
    await message.answer("📝 Iltimos, ismni <b>matn</b> ko'rinishida yozing:")
    await message.answer(NAME_PROMPT)


async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
