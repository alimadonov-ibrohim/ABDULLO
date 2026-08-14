import asyncio
from aiogram import Bot

BOT_TOKEN = "8812859354:AAGD8J4VTucwkhHMsQWczfU5WZqjz70o-Ik"


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        me = await bot.get_me()
        print("BOT OK:", me.username, "-", me.first_name)
        print("Bot ishlayapti!")
    except Exception as e:
        print("XATOLIK:", e)
    finally:
        await bot.session.close()


asyncio.run(main())