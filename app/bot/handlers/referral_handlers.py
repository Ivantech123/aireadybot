from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from app.bot.utils import States, TelegramError
from app.services.db import DataBase, DatabaseError

class ReferralHandlers:
    def __init__(self, database: DataBase):
        self.database = database
        # Бонусы за рефералов
        self.referral_bonuses = {
            'chatgpt': 5000,  # токенов
            'dall_e': 5,     # генераций
            'stable': 5,     # генераций
            'midjourney': 5  # генераций
        }
    
    async def show_referral_program_handler(self, message: Message, state: FSMContext):
        """Показывает информацию о реферальной программе"""
        try:
            user_id = message.from_user.id
            bot_username = (await message.bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
            
            # Получаем список рефералов пользователя
            referrals = await self.database.get_referrals(user_id)
            
            message_text = "🤝 Реферальная программа\n\n"
            message_text += "Приглашайте друзей в бота и получайте бонусы!\n\n"
            message_text += "За каждого приглашенного пользователя, который начнет использовать бота, вы получите:\n"
            message_text += f"💬 +{self.referral_bonuses['chatgpt']} токенов ChatGPT\n"
            message_text += f"🌄 +{self.referral_bonuses['dall_e']} генераций DALL·E\n"
            message_text += f"🌅 +{self.referral_bonuses['stable']} генераций Stable Diffusion\n"
            message_text += f"🖼 +{self.referral_bonuses['midjourney']} генераций MidJourney\n\n"
            
            message_text += f"Ваша реферальная ссылка:\n{referral_link}\n\n"
            
            # Информация о приглашенных пользователях
            message_text += f"👥 Приглашено пользователей: {len(referrals)}\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Список рефералов", callback_data="show_referrals_list")],
                [InlineKeyboardButton(text="📱 Поделиться ссылкой", switch_inline_query=f"Попробуй нашего бота с ИИ! {referral_link}")]
            ])
            
            await message.answer(message_text, reply_markup=keyboard)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def show_referrals_list_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Показывает список рефералов пользователя"""
        try:
            await callback_query.answer()
            
            user_id = callback_query.from_user.id
            referrals = await self.database.get_referrals(user_id)
            
            if not referrals:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_referral_program")]
                ])
                
                await callback_query.message.edit_text(
                    "👥 Список ваших рефералов\n\n"
                    "У вас пока нет приглашенных пользователей.\n\n"
                    "Поделитесь своей реферальной ссылкой с друзьями, чтобы получать бонусы!",
                    reply_markup=keyboard
                )
                return
            
            message_text = "👥 Список ваших рефералов\n\n"
            
            for i, referral in enumerate(referrals, 1):
                referred_id = referral[0]
                joined_date = referral[1].strftime("%d.%m.%Y")
                bonus_given = "✅" if referral[2] else "⏳"
                
                message_text += f"{i}. ID: {referred_id} | Дата: {joined_date} | Бонус: {bonus_given}\n"
            
            message_text += "\n✅ - бонус получен, ⏳ - в обработке\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_referral_program")]
            ])
            
            await callback_query.message.edit_text(message_text, reply_markup=keyboard)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def back_to_referral_program_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Возвращает к основной информации о реферальной программе"""
        try:
            await callback_query.answer()
            await self.show_referral_program_handler(callback_query.message, state)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def process_referral_start(self, message: Message, referrer_id: int, state: FSMContext):
        """Обрабатывает начало работы с ботом по реферальной ссылке"""
        try:
            user_id = message.from_user.id
            
            # Проверяем, что пользователь не пытается пригласить сам себя
            if user_id == referrer_id:
                return False
            
            # Проверяем, существует ли реферрер
            referrer_exists = await self.database.is_user(referrer_id)
            if not referrer_exists:
                return False
            
            # Проверяем, существует ли пользователь в базе
            user_exists = await self.database.is_user(user_id)
            
            if not user_exists:
                # Если пользователь новый, добавляем его с referrer_id
                await self.database.insert_user(user_id, referrer_id)
                
                # Отправляем сообщение рефереру о приглашенном пользователе
                try:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎉 Поздравляем! Новый пользователь присоединился по вашей реферальной ссылке.\n"
                        f"Скоро вы получите бонусы за приглашение!"
                    )
                except Exception:
                    # Если не можем отправить сообщение реферреру, просто игнорируем ошибку
                    pass
                
                return True
            
            return False
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            return False
