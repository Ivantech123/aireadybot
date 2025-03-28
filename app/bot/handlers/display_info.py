from app.bot.utils import States, TelegramError

from aiogram import types

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.services.db import DataBase, DatabaseError

class DisplayInfo:
    def __init__(self, database: DataBase):
        self.database = database

    async def display_info_handler(self, message: types.Message, state: FSMContext):
        try:
            user_id = message.from_user.id
            result = await self.database.get_userinfo(user_id)

            button = [[types.KeyboardButton(text="💫Buy tokens and generations")], [types.KeyboardButton(text="🔙Back")]]
            reply_markup = types.ReplyKeyboardMarkup(
                keyboard = button, resize_keyboard=True
            )
            await message.answer(
                text = f"You have: \n 💭{result[0]} ChatGPT tokens \n 🌄{result[1]} DALL·E generations \n 🌅{result[2]} Stable Diffusion generations \n 🖼️{result[3]} MidJourney generations \n\n 💫 You can buy more using Telegram Stars",
                reply_markup=reply_markup,
            )
            
            # Show subscription options
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💬 Chat plans", callback_data="show_chat_plans")],
                [types.InlineKeyboardButton(text="🖼 Image plans", callback_data="show_image_plans")],
                [types.InlineKeyboardButton(text="💫 My stars balance", callback_data="stars_balance")]
            ])
            
            await message.answer(
                "Select a subscription plan:",
                reply_markup=keyboard
            )
            
            await state.set_state(States.INFO_STATE)
        except DatabaseError:
            raise DatabaseError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err