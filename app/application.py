import sys
import os
import asyncio

# Исправление для работы в Windows - устанавливаем WindowsSelectorEventLoopPolicy
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Добавляем корневую директорию в путь Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.db import DataBase
from app.services.cryptopay import CryptoPay
from app.services.openaitools import OpenAiTools
from app.services.stablediffusion import StableDiffusion
from app.services.midjourney import MidJourney
from app.services.telegram_stars import TelegramStarsService

from dotenv import load_dotenv

import os

from fastapi import FastAPI, APIRouter
import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from app.bot.setup import register_handlers

from app.api.setup import register_routes

from app.core.database import DataBaseCore

async def main():
    print("=== Запуск бота в режиме polling ===")
    load_dotenv()

    dp = Dispatcher()

    database_core = DataBaseCore(os.getenv("DATABASE_URL"))
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

    database = DataBase(database_core.pool)

    openai = OpenAiTools(os.getenv("OPENAI_API_KEY"))

    stable = StableDiffusion(os.getenv("STABLE_DIFFUSION_API_KEY"))
    
    midjourney = MidJourney(os.getenv("MIDJOURNEY_API_KEY"))
    
    cryptopay = CryptoPay(os.getenv("CRYPTOPAY_KEY"))
    
    telegram_stars = TelegramStarsService(
        api_id=int(os.getenv("TELEGRAM_API_ID")),
        api_hash=os.getenv("TELEGRAM_API_HASH"),
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
    )

    register_handlers(dp, database, openai, stable, cryptopay, midjourney, telegram_stars)

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    print("=== Инициализация базы данных и Telegram Stars ===")
    await database_core.open_pool()
    await database.create_tables()
    # Инициализируем клиент Telethon для Telegram Stars
    await telegram_stars.init_client()
    
    print("=== Запуск polling для приема сообщений ===")
    # Вместо установки webhook используем polling
    await dp.start_polling(bot)

def run():
    print("=== Запуск бота ===")
    load_dotenv()

    dp = Dispatcher()

    app = FastAPI()

    cryptopay = CryptoPay(os.getenv("CRYPTOPAY_KEY"))

    database_core = DataBaseCore(os.getenv("DATABASE_URL"))
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

    database = DataBase(database_core.pool)

    openai = OpenAiTools(os.getenv("OPENAI_API_KEY"))

    stable = StableDiffusion(os.getenv("STABLE_DIFFUSION_API_KEY"))
    
    midjourney = MidJourney(os.getenv("MIDJOURNEY_API_KEY"))
    
    telegram_stars = TelegramStarsService(
        api_id=int(os.getenv("TELEGRAM_API_ID")),
        api_hash=os.getenv("TELEGRAM_API_HASH"),
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
    )

    register_handlers(dp, database, openai, stable, cryptopay, midjourney, telegram_stars)

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    router = APIRouter()

    register_routes(router, database, dp, bot, os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("CRYPTOPAY_KEY"))

    app.include_router(router)

    def on_startup_handler(database_core: DataBaseCore, database: DataBase, telegram_stars: TelegramStarsService):
        async def on_startup() -> None:
            print("=== Инициализация базы данных и Telegram Stars ===")
            await database_core.open_pool()
            await database.create_tables()
            # Инициализируем клиент Telethon для Telegram Stars
            await telegram_stars.init_client()
            url_webhook = os.getenv("BASE_WEBHOOK_URL") + os.getenv("TELEGRAM_BOT_TOKEN")
            await bot.set_webhook(url=url_webhook)
            print("=== Бот успешно запущен ===")
        return on_startup

    app.add_event_handler("startup", on_startup_handler(database_core, database, telegram_stars))

    print("=== Запуск веб-сервера ===")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Запускаем в режиме polling
    asyncio.run(main())
