import os
import asyncio
from aiogram import Bot
from dotenv import load_dotenv

async def delete_webhook():
    load_dotenv()
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await bot.delete_webhook()
    print("Webhook успешно удален!")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(delete_webhook())
