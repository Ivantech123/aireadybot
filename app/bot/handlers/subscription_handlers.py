from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from app.bot.utils import States, TelegramError
from app.services.db import DataBase, DatabaseError
from app.services.telegram_stars import TelegramStarsService, TelegramStarsError

class SubscriptionHandlers:
    def __init__(self, database: DataBase, telegram_stars: TelegramStarsService):
        self.database = database
        self.telegram_stars = telegram_stars
        # уプレделение тарифных планов
        self.chat_plans = {
            "starter": {
                "name": "Стартовый",
                "price": 100,  # звезд
                "daily_limit": 20,  # сообщений в день
                "duration": 7,  # дней
                "description": "+20 сообщений в день\nСрок действия: 7 дней"
            },
            "advanced": {
                "name": "Продвинутый",
                "price": 250,  # звезд
                "daily_limit": 50,  # сообщений в день
                "duration": 14,  # дней
                "description": "+50 сообщений в день\nСрок действия: 14 дней"
            },
            "expert": {
                "name": "Эксперт",
                "price": 450,  # звезд
                "daily_limit": 999999,  # безлимит
                "duration": 30,  # дней
                "description": "Безлимитное сообщений\nСрок действия: 30 дней"
            }
        }
        
        self.image_plans = {
            "mini": {
                "name": "Мини",
                "price": 80,  # звезд
                "daily_limit": 5,  # картинок в день
                "duration": 7,  # дней
                "description": "+5 картинок в день\nСрок действия: 7 дней"
            },
            "standard": {
                "name": "Стандарт",
                "price": 180,  # звезд
                "daily_limit": 15,  # картинок в день
                "duration": 14,  # дней
                "description": "+15 картинок в день\nСрок действия: 14 дней"
            },
            "maximum": {
                "name": "Максимум",
                "price": 350,  # звезд
                "daily_limit": 30,  # картинок в день
                "duration": 30,  # дней
                "description": "+30 картинок в день\nСрок действия: 30 дней"
            }
        }

    async def show_subscriptions_handler(self, message: Message, state: FSMContext):
        """Показывает доступные типы подписок"""
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Тарифы для чата", callback_data="show_chat_plans")],
                [InlineKeyboardButton(text="🖼 Тарифы для генерации картинок", callback_data="show_image_plans")],
                [InlineKeyboardButton(text="💫 Мой баланс звезд", callback_data="stars_balance")]
            ])
            
            await message.answer(
                "Выберите тип подписки:",
                reply_markup=keyboard
            )
            await state.set_state(States.SUBSCRIPTION_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def show_chat_plans_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Показывает тарифы для чата"""
        try:
            await callback_query.answer()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"«{self.chat_plans['starter']['name']}» — {self.chat_plans['starter']['price']} звёзд", 
                    callback_data="buy_chat_starter"
                )],
                [InlineKeyboardButton(
                    text=f"«{self.chat_plans['advanced']['name']}» — {self.chat_plans['advanced']['price']} звёзд", 
                    callback_data="buy_chat_advanced"
                )],
                [InlineKeyboardButton(
                    text=f"«{self.chat_plans['expert']['name']}» — {self.chat_plans['expert']['price']} звёзд", 
                    callback_data="buy_chat_expert"
                )],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_subscriptions")]
            ])
            
            message_text = "💬 Тарифы для чата (текстовые и голосовые вопросы):\n\n"
            for plan_id, plan in self.chat_plans.items():
                message_text += f"«{plan['name']}» — {plan['price']} звёзд\n{plan['description']}\n\n"
            
            await callback_query.message.edit_text(
                message_text,
                reply_markup=keyboard
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def show_image_plans_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Показывает тарифы для генерации картинок"""
        try:
            await callback_query.answer()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"«{self.image_plans['mini']['name']}» — {self.image_plans['mini']['price']} звёзд", 
                    callback_data="buy_image_mini"
                )],
                [InlineKeyboardButton(
                    text=f"«{self.image_plans['standard']['name']}» — {self.image_plans['standard']['price']} звёзд", 
                    callback_data="buy_image_standard"
                )],
                [InlineKeyboardButton(
                    text=f"«{self.image_plans['maximum']['name']}» — {self.image_plans['maximum']['price']} звёзд", 
                    callback_data="buy_image_maximum"
                )],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_subscriptions")]
            ])
            
            message_text = "🖼 Тарифы для генерации картинок:\n\n"
            for plan_id, plan in self.image_plans.items():
                message_text += f"«{plan['name']}» — {plan['price']} звёзд\n{plan['description']}\n\n"
            
            await callback_query.message.edit_text(
                message_text,
                reply_markup=keyboard
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def back_to_subscriptions_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Возвращает к выбору типа подписки"""
        try:
            await callback_query.answer()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Тарифы для чата", callback_data="show_chat_plans")],
                [InlineKeyboardButton(text="🖼 Тарифы для генерации картинок", callback_data="show_image_plans")],
                [InlineKeyboardButton(text="💫 Мой баланс звезд", callback_data="stars_balance")]
            ])
            
            await callback_query.message.edit_text(
                "Выберите тип подписки:",
                reply_markup=keyboard
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def buy_subscription_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обрабатывает покупку подписки"""
        try:
            await callback_query.answer()
            
            # Получаем ID пользователя
            user_id = callback_query.from_user.id
            
            # Получаем данные о плане из callback_data
            callback_data = callback_query.data
            plan_type, plan_id = callback_data.replace('buy_', '').split('_')
            
            # Получаем информацию о плане
            if plan_type == 'chat':
                plan = self.chat_plans[plan_id]
                sub_type = "chat"
            else:  # plan_type == 'image'
                plan = self.image_plans[plan_id]
                sub_type = "image"
            
            # Проверяем баланс звезд пользователя
            stars_balance = await self.telegram_stars.get_user_stars_balance(user_id)
            
            if stars_balance < plan['price']:
                # Если баланса не хватает, предлагаем купить звезды
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💸 Купить звезды", url="tg://stars/buy")],
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"show_{plan_type}_plans")]
                ])
                
                await callback_query.message.edit_text(
                    f"❌ Недостаточно звезд для покупки тарифа «{plan['name']}».\n\n" \
                    f"Текущий баланс: {stars_balance} 💫\n" \
                    f"Необходимо: {plan['price']} 💫\n\n" \
                    f"Пополните баланс звезд, чтобы продолжить.",
                    reply_markup=keyboard
                )
                return
            
            # Если баланса хватает, предлагаем подтвердить покупку
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✔️ Подтвердить", callback_data=f"confirm_{plan_type}_{plan_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=f"show_{plan_type}_plans")]
            ])
            
            await callback_query.message.edit_text(
                f"💫 Подтверждение покупки\n\n" \
                f"Тариф: «{plan['name']}»\n" \
                f"Цена: {plan['price']} звёзд\n" \
                f"Описание: {plan['description']}\n\n" \
                f"Текущий баланс: {stars_balance} 💫\n" \
                f"Баланс после покупки: {stars_balance - plan['price']} 💫\n\n" \
                f"Подтвердите покупку:",
                reply_markup=keyboard
            )
        except TelegramStarsError:
            raise TelegramStarsError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def confirm_subscription_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждает покупку подписки"""
        try:
            await callback_query.answer()
            
            # Получаем ID пользователя
            user_id = callback_query.from_user.id
            
            # Получаем данные о плане из callback_data
            callback_data = callback_query.data
            plan_type, plan_id = callback_data.replace('confirm_', '').split('_')
            
            # Получаем информацию о плане
            if plan_type == 'chat':
                plan = self.chat_plans[plan_id]
                sub_type = "chat"
            else:  # plan_type == 'image'
                plan = self.image_plans[plan_id]
                sub_type = "image"
            
            # Списываем звезды через API
            success, message = await self.telegram_stars.deduct_stars(
                user_id, 
                plan['price'], 
                f"Подписка на тариф «{plan['name']}» ({sub_type})"
            )
            
            if not success:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"show_{plan_type}_plans")]
                ])
                
                await callback_query.message.edit_text(
                    f"❌ Ошибка при списании звезд: {message}\n\nПопробуйте позже.",
                    reply_markup=keyboard
                )
                return
            
            # Добавляем подписку в базу данных
            await self.database.create_subscription(
                user_id,
                sub_type,
                plan_id,
                plan['daily_limit'],
                plan['duration']
            )
            
            # Отправляем подтверждение успешной покупки
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К тарифам", callback_data=f"show_{plan_type}_plans")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
            ])
            
            await callback_query.message.edit_text(
                f"✅ Поздравляем! Вы успешно приобрели тариф «{plan['name']}».\n\n" \
                f"Тип: {sub_type.capitalize()}\n" \
                f"Ежедневный лимит: {plan['daily_limit'] if plan['daily_limit'] < 999999 else 'Безлимитно'}\n" \
                f"Срок действия: {plan['duration']} дней\n\n" \
                f"Спасибо за поддержку нашего бота! 🚀",
                reply_markup=keyboard
            )
        except DatabaseError:
            raise DatabaseError
        except TelegramStarsError:
            raise TelegramStarsError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def check_subscription_status_handler(self, message: Message, state: FSMContext):
        """Показывает статус подписок пользователя"""
        try:
            user_id = message.from_user.id
            
            # Получаем информацию о подписках пользователя
            chat_sub = await self.database.check_subscription(user_id, "chat")
            image_sub = await self.database.check_subscription(user_id, "image")
            
            message_text = "📊 Статус ваших подписок:\n\n"
            
            if chat_sub:
                plan_id = chat_sub['plan']
                plan_name = self.chat_plans[plan_id]['name'] if plan_id in self.chat_plans else plan_id.capitalize()
                end_date = chat_sub['end_date'].strftime("%d.%m.%Y")
                
                message_text += f"💬 Чат: Тариф «{plan_name}»\n" \
                               f"Лимит: {chat_sub['daily_limit']} сообщений в день\n" \
                               f"Использовано сегодня: {chat_sub['usage_today']}\n" \
                               f"Действует до: {end_date}\n\n"
            else:
                message_text += "💬 Чат: Подписка отсутствует\n\n"
            
            if image_sub:
                plan_id = image_sub['plan']
                plan_name = self.image_plans[plan_id]['name'] if plan_id in self.image_plans else plan_id.capitalize()
                end_date = image_sub['end_date'].strftime("%d.%m.%Y")
                
                message_text += f"🖼 Картинки: Тариф «{plan_name}»\n" \
                               f"Лимит: {image_sub['daily_limit']} картинок в день\n" \
                               f"Использовано сегодня: {image_sub['usage_today']}\n" \
                               f"Действует до: {end_date}\n\n"
            else:
                message_text += "🖼 Картинки: Подписка отсутствует\n\n"
            
            # Добавляем кнопку для покупки подписок
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Купить подписку", callback_data="show_subscriptions")],
                [InlineKeyboardButton(text="⭐️ Пополнить баланс звезд", url="tg://stars/buy")]
            ])
            
            await message.answer(message_text, reply_markup=keyboard)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def stars_balance_handler(self, callback_query: types.CallbackQuery):
        """Показывает баланс звезд пользователя"""
        try:
            await callback_query.answer()
            user_id = callback_query.from_user.id
            balance = await self.telegram_stars.get_user_stars_balance(user_id)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐️ Купить звезды", url="tg://stars/buy")],
                [InlineKeyboardButton(text="🔙 К подпискам", callback_data="back_to_subscriptions")]
            ])
            
            await callback_query.message.edit_text(
                f"💫 Ваш баланс звезд Telegram: {balance} ⭐️\n\n" \
                f"Для покупки звезд используйте официальный интерфейс Telegram.",
                reply_markup=keyboard
            )
        except TelegramStarsError:
            raise TelegramStarsError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
