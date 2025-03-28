from app.bot.utils import States, TelegramError

from aiogram import types

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from app.services.db import DataBase, DatabaseError
from app.bot.handlers.referral_handlers import ReferralHandlers

class StartHandler:
    def __init__(self, database: DataBase):
        self.database = database
        self.referral_handlers = ReferralHandlers(database)

    async def start_handler(self, message: types.Message, state: FSMContext):
        try:
            user_id = message.from_user.id
            result = await self.database.is_user(user_id)
            
            # Проверяем, есть ли реферальный код в команде /start
            referrer_id = None
            if message.text and len(message.text.split()) > 1:
                param = message.text.split()[1]
                if param.startswith('ref'):
                    try:
                        referrer_id = int(param[3:])
                    except ValueError:
                        referrer_id = None
            
            # Добавляем новую кнопку для MidJourney
            button = [[KeyboardButton(text="💭Chatting — ChatGPT-4o")],
                      [KeyboardButton(text="🌄Image generation — DALL·E 3")],
                      [KeyboardButton(text="🌅Image generation — Stable Diffusion 3")],
                      [KeyboardButton(text="🖼️Images — MidJourney")],
                      [KeyboardButton(text="📊Subscriptions")],
                      [KeyboardButton(text="📈Referral program")],
                      [KeyboardButton(text="👤My account | 💰Buy")]]
            reply_markup = ReplyKeyboardMarkup(
                keyboard = button, resize_keyboard=True
            )
            await self.database.delete_messages(user_id)
            
            if not result:
                # Если пользователь новый и есть реферальный код
                if referrer_id:
                    await self.database.insert_user(user_id, referrer_id)
                    # Обрабатываем реферальный код
                    await self.referral_handlers.process_referral_start(message, referrer_id, state)
                else:
                    await self.database.insert_user(user_id)
                
                await message.answer(
                    text = "👋Вам доступно: \n💭3000 токенов ChatGPT \n🌄3 генерации DALL·E \n🌅3 генерации Stable Diffusion\n🖼️3 генерации MidJourney\n Выберите опцию: 👇 \n Если кнопки не работают, введите команду /start",
                    reply_markup=reply_markup,
                )
            else:
                await message.answer(
                    text = "Выберите опцию: 👇🏻 \n Если кнопки не работают, введите команду /start",
                    reply_markup=reply_markup,
                )
            await state.set_state(States.ENTRY_STATE)
        except DatabaseError:
            raise DatabaseError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err