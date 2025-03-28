from aiogram import types
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from app.bot.utils import States, TelegramError
from app.services.db import DataBase, DatabaseError
from app.services.telegram_stars import TelegramStarsService, TelegramStarsError

class TelegramStarsHandlers:
    def __init__(self, database: DataBase, telegram_stars: TelegramStarsService):
        self.database = database
        self.telegram_stars = telegram_stars
        
    async def send_invoice_handler(self, message: Message, state: FSMContext):
        try:
            user_id = message.from_user.id
            current_state = await state.get_state()
            
            title = ""
            description = ""
            amount = 0
            product_type = ""
            
            if current_state == States.PURCHASE_CHATGPT_STATE:
                title = "100K ChatGPT токенов"
                description = "Приобретение 100K токенов для ChatGPT"
                amount = 20  # Цена в звездах
                product_type = "chatgpt"
            elif current_state == States.PURCHASE_DALL_E_STATE:
                title = "50 генераций DALL·E"
                description = "Приобретение 50 генераций изображений DALL·E"
                amount = 20  # Цена в звездах
                product_type = "dall_e"
            elif current_state == States.PURCHASE_STABLE_STATE:
                title = "50 генераций Stable Diffusion"
                description = "Приобретение 50 генераций изображений Stable Diffusion"
                amount = 20  # Цена в звездах
                product_type = "stable"
            elif current_state == States.PURCHASE_MIDJOURNEY_STATE:
                title = "50 генераций MidJourney"
                description = "Приобретение 50 генераций изображений MidJourney"
                amount = 20  # Цена в звездах
                product_type = "midjourney"
            
            prices = [LabeledPrice(label="XTR", amount=amount)]
            await message.answer_invoice(
                title=title,
                description=description,
                prices=prices,
                provider_token="",  # Для Telegram Stars передаем пустую строку
                payload=product_type,
                currency="XTR",
                reply_markup=self.get_payment_keyboard(amount),
            )
        except TelegramStarsError:
            raise TelegramStarsError
        except DatabaseError:
            raise DatabaseError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
            
    async def pre_checkout_handler(self, pre_checkout_query: PreCheckoutQuery):
        try:
            # Проверяем транзакцию и подтверждаем её
            await pre_checkout_query.answer(ok=True)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
            
    async def success_payment_handler(self, message: Message):
        try:
            user_id = message.from_user.id
            payment_info = message.successful_payment
            product_type = payment_info.invoice_payload
            telegram_payment_charge_id = payment_info.telegram_payment_charge_id
            
            # Обработка успешной оплаты в зависимости от типа продукта
            await self.process_successful_payment(user_id, product_type)
            
            # Отправляем пользователю подтверждение
            product_name = {
                "chatgpt": "100K ChatGPT токенов",
                "dall_e": "50 генераций DALL·E",
                "stable": "50 генераций Stable Diffusion",
                "midjourney": "50 генераций MidJourney"
            }.get(product_type, "товар")
            
            await message.answer(f"✅ Спасибо за покупку! Вы успешно приобрели {product_name}.")
        except DatabaseError:
            raise DatabaseError
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
            
    async def process_successful_payment(self, user_id: int, product_type: str):
        try:
            if product_type == "chatgpt":
                await self.database.update_chatgpt(user_id, 0)  # Не используем invoice_id
            elif product_type == "dall_e":
                await self.database.update_dalle(user_id, 0)  # Не используем invoice_id
            elif product_type == "stable":
                await self.database.update_stable(user_id, 0)  # Не используем invoice_id
            elif product_type == "midjourney":
                await self.database.update_midjourney(user_id, 0)  # Не используем invoice_id
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
            
    def get_payment_keyboard(self, amount):
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Оплатить {amount} ⭐️", pay=True)
        return builder.as_markup()
    
    async def stars_menu_handler(self, message: Message, state: FSMContext):
        """Обработчик для меню звезд Telegram"""
        try:
            # Создаем клавиатуру корректным способом
            button1 = types.KeyboardButton(text="🔍 100K ChatGPT tokens - 20 stars")
            button2 = types.KeyboardButton(text="🌄 50 DALL·E image generations - 20 stars")
            button3 = types.KeyboardButton(text="🌅 50 Stable Diffusion image generations - 20 stars")
            button4 = types.KeyboardButton(text="🖼️ 50 MidJourney image generations - 20 stars")
            button5 = types.KeyboardButton(text="🔎Check balance")
            button6 = types.KeyboardButton(text="🔙Back")
            
            keyboard = types.ReplyKeyboardMarkup(keyboard=[[button1], [button2], [button3], [button4], [button5], [button6]], resize_keyboard=True)

            # Получаем баланс звезд
            user_id = message.from_user.id
            stars_balance = await self.telegram_stars.get_user_stars_balance(user_id)
            
            await message.answer(
                f"💫 Your stars balance: *{stars_balance}* stars\n\n"
                f"You can buy Telegram Stars by clicking the button below to open the purchase page:\n\n"
                f"👉 [Buy stars](tg://stars/buy) 👈\n\n"
                f"Or select an item to purchase:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            await state.set_state(States.TELEGRAM_STARS_MENU_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            await message.answer(f"Error loading stars menu: {str(e)}")

    async def check_stars_balance(self, message: Message, state: FSMContext):
        """Обработчик для проверки баланса звезд"""
        try:
            user_id = message.from_user.id
            stars_balance = await self.telegram_stars.get_user_stars_balance(user_id)
            
            # Создаем клавиатуру для покупки звезд
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                text="🛍️ Buy stars", 
                url="tg://stars/buy"
            ))
            
            await message.answer(
                f"💫 *Your stars balance: {stars_balance} stars*\n\n"
                f"You can use stars to purchase tokens and image generations.\n"
                f"Need more stars? Click the button below.", 
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            await message.answer(f"Error checking stars balance: {str(e)}")

    async def stars_balance_handler(self, message: Message, state: FSMContext):
        """Обработчик для команды /stars"""
        await self.check_stars_balance(message, state)

    async def buy_stars_handler(self, message: Message, state: FSMContext):
        """Обработчик для команды /buy"""
        try:
            # Создаем клавиатуру для покупки звезд
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                text="🛍️ Buy Telegram Stars", 
                url="tg://stars/buy"
            ))
            
            await message.answer(
                f"🛍️ *Buy Telegram Stars*\n\n"
                f"Telegram Stars are a universal currency for bots and mini apps.\n"
                f"You can use them to purchase:\n"
                f"- 🤖 ChatGPT tokens\n"
                f"- 🌄 DALL-E image generations\n"
                f"- 🌅 Stable Diffusion image generations\n"
                f"- 🖼️ MidJourney image generations\n\n"
                f"To purchase stars, click the button below:", 
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            await message.answer(f"Error with stars purchase: {str(e)}")
    
    async def paysupport_handler(self, message: Message):
        try:
            await message.answer(
                "ℹ️ Информация о платежах и возвратах:\n\n"
                "1. Все покупки за звезды Telegram являются окончательными.\n"
                "2. Возврат средств возможен только в исключительных случаях.\n"
                "3. Для обсуждения возврата звезд, пожалуйста, свяжитесь с администрацией бота.\n\n"
                "Спасибо за понимание!"
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def check_stars_balance_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработчик для проверки баланса звезд Telegram"""
        try:
            await callback_query.answer()
            user_id = callback_query.from_user.id
            
            # Получаем баланс звезд пользователя
            try:
                balance = await self.telegram_stars.get_user_stars_balance(user_id)
                
                # Создаем клавиатуру с кнопкой для покупки звезд
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🛍️ Buy stars", callback_data="buy_stars")],
                    [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                ])
                
                await callback_query.message.edit_text(
                    f"💫 *Your stars balance: {balance} stars*\n\n"
                    "Stars are a universal currency for bots and mini apps.",
                    reply_markup=keyboard
                )
            except TelegramStarsError as e:
                # Если произошла ошибка при получении баланса
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🛍️ Buy stars", callback_data="buy_stars")],
                    [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                ])
                
                await callback_query.message.edit_text(
                    "❌ Failed to get stars balance. Please try again later.\n\n"
                    "You can buy Telegram Stars through the official interface.",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def pay_with_stars_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработчик для оплаты услуг звездами Telegram"""
        try:
            await callback_query.answer()
            user_id = callback_query.from_user.id
            
            # Получаем данные о продукте из callback data
            data = callback_query.data
            product_type = data.replace("pay_stars_", "")
            
            # Определяем стоимость и название продукта
            product_info = {
                "chatgpt": {"name": "100K ChatGPT токенов", "price": 20, "amount": 100000},
                "dall_e": {"name": "50 генераций DALL·E", "price": 20, "amount": 50},
                "stable": {"name": "50 генераций Stable Diffusion", "price": 20, "amount": 50},
                "midjourney": {"name": "50 генераций MidJourney", "price": 20, "amount": 50}
            }
            
            if product_type not in product_info:
                await callback_query.message.edit_text("❌ Unknown product type.")
                return
                
            product = product_info[product_type]
            price = product["price"]
            name = product["name"]
            amount = product["amount"]
            
            # Проверяем баланс звезд пользователя
            try:
                balance = await self.telegram_stars.get_user_stars_balance(user_id)
                
                if balance < price:
                    # Недостаточно звезд
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🛍️ Buy stars", callback_data="buy_stars")],
                        [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ])
                    
                    await callback_query.message.edit_text(
                        f"❌ Not enough stars to buy {name}.\n\n"
                        f"Cost: {price} stars\n"
                        f"Your balance: {balance} stars\n\n"
                        "You can buy more stars through the official Telegram interface.",
                        reply_markup=keyboard
                    )
                    return
                
                # Отправляем запрос на списание звезд
                invoice_id = await self.telegram_stars.deduct_stars(user_id, price, f"Покупка {name}")
                
                # Клавиатура для проверки статуса списания
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔄 Check status", callback_data=f"check_payment_{invoice_id}")],
                    [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                ])
                
                # Обновляем сообщение
                await callback_query.message.edit_text(
                    f"🔄 Processing purchase of {name}...\n\n"
                    f"Cost: {price} stars\n"
                    "Please wait while the operation is completed.",
                    reply_markup=keyboard
                )
                
                # Обновляем баланс пользователя в системе
                if product_type == "chatgpt":
                    current_balance = await self.database.get_chatgpt(user_id)
                    await self.database.set_chatgpt(user_id, current_balance + amount)
                elif product_type == "dall_e":
                    current_balance = await self.database.get_dalle(user_id)
                    await self.database.set_dalle(user_id, current_balance + amount)
                elif product_type == "stable":
                    current_balance = await self.database.get_stable(user_id)
                    await self.database.set_stable(user_id, current_balance + amount)
                elif product_type == "midjourney":
                    current_balance = await self.database.get_midjourney(user_id)
                    await self.database.set_midjourney(user_id, current_balance + amount)
                
                # Отправляем уведомление о успешной покупке
                await callback_query.message.edit_text(
                    f"✅ Congratulations! You have successfully purchased {name}.\n\n"
                    f"Deducted: {price} stars\n"
                    f"Current stars balance: {balance - price} stars",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔙 Back to menu", callback_data="back_to_menu")]
                    ])
                )
                
            except TelegramStarsError as e:
                # Ошибка при получении баланса или списании звезд
                await callback_query.message.edit_text(
                    f"❌ Payment error: {str(e)}\n\n"
                    "Please try again or contact support.",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ])
                )
                
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err

    async def back_to_menu_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработчик для возврата в главное меню"""
        try:
            await callback_query.answer()
            
            # Создаем клавиатуру главного меню
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💬 Chat plans", callback_data="show_chat_plans")],
                [types.InlineKeyboardButton(text="🖼 Image plans", callback_data="show_image_plans")],
                [types.InlineKeyboardButton(text="💫 My stars balance", callback_data="stars_balance")]
            ])
            
            await callback_query.message.edit_text(
                "Select an action:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def check_payment_status_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработчик для проверки статуса платежа"""
        try:
            await callback_query.answer()
            
            # Получаем ID инвойса из callback data
            data = callback_query.data
            invoice_id = data.replace("check_payment_", "")
            
            try:
                # Проверяем статус платежа
                payment_status = await self.telegram_stars.check_payment_status(invoice_id)
                
                if payment_status['status'] == 'completed':
                    # Платеж успешно завершен
                    await callback_query.message.edit_text(
                        "✅ Payment successfully completed!\n\n"
                        "Your balance has been updated.",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔙 Back to menu", callback_data="back_to_menu")]
                        ])
                    )
                elif payment_status['status'] == 'pending':
                    # Платеж все еще обрабатывается
                    await callback_query.message.edit_text(
                        "⏳ Payment is still being processed...\n\n"
                        "Please check the status later.",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔄 Check again", callback_data=f"check_payment_{invoice_id}")],
                            [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                        ])
                    )
                else:
                    # Платеж отклонен или возникла ошибка
                    await callback_query.message.edit_text(
                        f"❌ Payment error: {payment_status['status']}\n\n"
                        "Please try again or contact support.",
                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                        ])
                    )
            except TelegramStarsError as e:
                # Ошибка при проверке статуса платежа
                await callback_query.message.edit_text(
                    f"❌ Failed to check payment status: {str(e)}\n\n"
                    "Please try again later.",
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ])
                )
                
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
