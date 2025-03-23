from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes, ConversationHandler
import logging
import asyncio
import time

from bot.services.telegram_stars_service import TelegramStarsService
from bot.services.user_service import UserService
from bot.services.subscription_service import SubscriptionService
from database.models import SubscriptionPlan
from database.db import get_session

logger = logging.getLogger(__name__)

# Conversation states
TELEGRAM_STARS_MENU, TELEGRAM_STARS_PURCHASE = range(2)

async def telegram_stars_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /stars command"""
    user = update.effective_user
    
    # Get user's Telegram Stars balance
    balance = await TelegramStarsService.get_stars_balance(user.id)
    
    # Create keyboard with options
    keyboard = [
        [InlineKeyboardButton("⭐️ Купить Telegram Stars", callback_data="buy_telegram_stars")],
        [InlineKeyboardButton("📊 Мой баланс", callback_data="check_telegram_stars_balance")]
    ]
    
    # Show balance if available
    if balance and hasattr(balance, 'balance'):
        await update.message.reply_text(
            f"⭐️ Ваш текущий баланс: *{balance.balance}* звезд Telegram\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⭐️ *Telegram Stars*\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return TELEGRAM_STARS_MENU

async def telegram_stars_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Telegram Stars menu selection"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "buy_telegram_stars":
        # Создаем красивое сообщение с инструкциями по покупке звезд Telegram
        message_text = (
            "🌟 *Покупка звезд Telegram* 🌟\n\n"
            "Для покупки звезд Telegram:\n\n"
            "1️⃣ Нажмите кнопку ниже для перехода в официальный интерфейс Telegram\n"
            "2️⃣ Выберите желаемое количество звезд\n"
            "3️⃣ Завершите покупку, следуя инструкциям\n\n"
            "После покупки вернитесь в этот чат и нажмите кнопку 'Проверить покупку'."
        )
        
        # Создаем клавиатуру с кнопками для покупки и проверки
        keyboard = [
            [InlineKeyboardButton("💫 Купить звезды Telegram", url="https://t.me/stars/buy")],
            [InlineKeyboardButton("✅ Проверить покупку", callback_data="check_stars_purchase")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stars_menu")]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return TELEGRAM_STARS_MENU
        
    elif callback_data == "check_stars_purchase":
        # Показываем анимацию проверки покупки
        await query.edit_message_text(
            "🔄 *Проверка покупки звезд Telegram...*",
            parse_mode="Markdown"
        )
        
        # Имитируем задержку для создания эффекта проверки
        await asyncio.sleep(2)
        
        # Получаем баланс звезд пользователя
        user = update.effective_user
        balance = await TelegramStarsService.get_stars_balance(user.id)
        
        if balance and hasattr(balance, 'balance'):
            # Создаем красивое сообщение с результатом проверки
            success_message = (
                "✅ *Проверка завершена!* ✅\n\n"
                f"Ваш текущий баланс: *{balance.balance}* звезд Telegram\n\n"
                "Спасибо за покупку! Теперь вы можете использовать звезды для подписки на планы."
            )
            
            keyboard = [
                [InlineKeyboardButton("📊 Мой баланс", callback_data="check_telegram_stars_balance")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stars_menu")]
            ]
            
            await query.edit_message_text(
                success_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если не удалось получить баланс
            error_message = (
                "❌ *Не удалось проверить покупку* ❌\n\n"
                "Возможные причины:\n"
                "• Покупка еще не завершена\n"
                "• Произошла ошибка при проверке баланса\n\n"
                "Пожалуйста, попробуйте еще раз через несколько минут."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_stars_purchase")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stars_menu")]
            ]
            
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        return TELEGRAM_STARS_MENU
    
    elif callback_data == "check_telegram_stars_balance":
        # Показываем анимацию проверки баланса
        await query.edit_message_text(
            "🔄 *Проверка баланса звезд Telegram...*",
            parse_mode="Markdown"
        )
        
        # Имитируем задержку для создания эффекта проверки
        await asyncio.sleep(1)
        
        # Получаем баланс звезд пользователя
        user = update.effective_user
        balance = await TelegramStarsService.get_stars_balance(user.id)
        
        if balance and hasattr(balance, 'balance'):
            # Создаем красивое сообщение с балансом
            balance_message = (
                "📊 *Баланс звезд Telegram* 📊\n\n"
                f"Ваш текущий баланс: *{balance.balance}* звезд Telegram\n\n"
                "Вы можете использовать звезды для подписки на планы или покупки других цифровых товаров и услуг."
            )
            
            keyboard = [
                [InlineKeyboardButton("⭐️ Купить еще звезд", callback_data="buy_telegram_stars")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stars_menu")]
            ]
            
            await query.edit_message_text(
                balance_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если не удалось получить баланс
            error_message = (
                "❌ *Не удалось проверить баланс* ❌\n\n"
                "Произошла ошибка при проверке баланса звезд Telegram.\n"
                "Пожалуйста, попробуйте еще раз позже."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="check_telegram_stars_balance")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stars_menu")]
            ]
            
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        return TELEGRAM_STARS_MENU
    
    elif callback_data == "back_to_stars_menu":
        # Возвращаемся в главное меню звезд
        user = update.effective_user
        balance = await TelegramStarsService.get_stars_balance(user.id)
        
        # Create keyboard with options
        keyboard = [
            [InlineKeyboardButton("⭐️ Купить Telegram Stars", callback_data="buy_telegram_stars")],
            [InlineKeyboardButton("📊 Мой баланс", callback_data="check_telegram_stars_balance")]
        ]
        
        # Show balance if available
        if balance and hasattr(balance, 'balance'):
            await query.edit_message_text(
                f"⭐️ Ваш текущий баланс: *{balance.balance}* звезд Telegram\n\n"
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "⭐️ *Telegram Stars*\n\n"
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        return TELEGRAM_STARS_MENU
    
    # Если получили неизвестную команду
    await query.edit_message_text(
        "❌ Неизвестная команда. Пожалуйста, попробуйте снова.",
        reply_markup=None
    )
    
    return ConversationHandler.END

async def create_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a Telegram Stars invoice"""
    try:
        # Get command arguments
        args = update.message.text.split()[1:]
        
        if not args:
            await update.message.reply_text(
                "❗️ Пожалуйста, укажите количество звезд для покупки.\n\n"
                "Пример: /buy_stars 10"
            )
            return
        
        try:
            amount = int(args[0])
            if amount <= 0:
                raise ValueError("Количество звезд должно быть положительным")
        except ValueError as e:
            await update.message.reply_text(
                f"❗️ Ошибка: {str(e)}. Пожалуйста, укажите целое положительное число."
            )
            return
        
        # Get user info
        user = update.effective_user
        user_id = user.id
        
        # Create invoice parameters
        title = f"Покупка {amount} звезд"
        description = f"Пополнение баланса на {amount} звезд Telegram для использования в боте"
        
        # Call service to prepare invoice
        invoice_result = await TelegramStarsService.deduct_stars(user_id, amount, description="Пополнение баланса")
        
        if not invoice_result['success']:
            await update.message.reply_text(
                f"❗️ Ошибка: {invoice_result['message']}"
            )
            return
        
        # Get invoice parameters
        invoice_params = invoice_result['invoice_params']
        
        # Store payload in context for verification in pre_checkout_callback
        context.user_data['payment_payload'] = invoice_params['payload']
        
        # Send invoice to user
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=invoice_params['title'],
            description=invoice_params['description'],
            payload=invoice_params['payload'],
            provider_token=None,  # Not needed for Telegram Stars
            currency=invoice_params['currency'],
            prices=invoice_params['prices'],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
            protect_content=False,
            send_email_to_provider=False,
            max_tip_amount=0,
            suggested_tip_amounts=[],
            provider_data=None,
            photo_url=None,
            photo_size=0,
            photo_width=0,
            photo_height=0,
            start_parameter=None
        )
        
        logger.info(f"Sent stars invoice to user {user_id} for {amount} stars")
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error creating stars invoice: {error_message}")
        logger.error(str(error_message))
        await update.message.reply_text(
            f"❗️ Произошла ошибка при создании инвойса. Пожалуйста, попробуйте снова."
        )

# Pre-checkout callback handler
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the pre-checkout callback"""
    query = update.pre_checkout_query
    
    try:
        # Verify that the payload matches what we sent
        stored_payload = context.user_data.get('payment_payload')
        
        if stored_payload and query.invoice_payload == stored_payload:
            logger.info(f"Pre-checkout query from user {query.from_user.id} verified successfully")
            # Accept the payment
            await query.answer(ok=True)
        else:
            logger.warning(f"Invalid payload in pre-checkout query from user {query.from_user.id}")
            logger.warning(f"Expected: {stored_payload}, Got: {query.invoice_payload}")
            # Reject the payment
            await query.answer(ok=False, error_message="Неверный идентификатор платежа")
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in pre-checkout callback: {error_message}")
        logger.error(str(error_message))
        # Reject the payment
        await query.answer(ok=False, error_message="Произошла ошибка при обработке платежа")

# Successful payment callback handler
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    try:
        payment = update.message.successful_payment
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Received successful payment from user {user_id}: {payment.total_amount / 100} {payment.currency}")
        
        # Process the payment using the service
        result = await TelegramStarsService.process_successful_payment(user_id, payment)
        
        if result['success']:
            # Determine message based on payment type
            if result.get('payment_type') == 'subscription':
                # This was a subscription payment
                subscription_info = result.get('subscription_info', {})
                plan_name = subscription_info.get('plan_name', 'Стандартный план')
                expiry_date = subscription_info.get('expiry_date', 'Не указана')
                daily_limit = subscription_info.get('daily_limit', 0)
                
                await update.message.reply_text(
                    f"✅ Подписка успешно активирована!\n\n" 
                    f"• План: {plan_name}\n"
                    f"• Действует до: {expiry_date}\n"
                    f"• Ежедневный лимит: {daily_limit} запросов\n\n"
                    "Спасибо за поддержку! Теперь вы можете использовать все возможности бота."
                )
            else:
                # This was a regular stars purchase
                amount = result.get('amount', payment.total_amount / 100)
                
                # Get updated balance
                balance_info = await TelegramStarsService.get_stars_balance(user_id)
                current_balance = balance_info.balance if balance_info and hasattr(balance_info, 'balance') else 'Неизвестно'
                
                await update.message.reply_text(
                    f"✅ Успешная оплата!\n\n"
                    f"• Пополнение: {amount} звезд\n"
                    f"• Текущий баланс: {current_balance} звезд\n\n"
                    "Спасибо за покупку! Теперь вы можете использовать звезды для подписки на планы или покупки других цифровых товаров и услуг."
                )
        else:
            # Payment processing failed
            await update.message.reply_text(
                f"❗️ Ошибка при обработке платежа: {result['message']}"
            )
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in successful payment callback: {error_message}")
        logger.error(str(error_message))
        await update.message.reply_text(
            "❗️ Произошла ошибка при обработке платежа. Пожалуйста, свяжитесь с администратором."
        )

# Check stars purchase handler
async def check_stars_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle check stars purchase button click"""
    query = update.callback_query
    await query.answer()
    
    # Get user ID
    user = update.effective_user
    telegram_id = user.id
    
    # Show loading animation
    loading_message = "⏳️ *Проверка баланса звезд...*"
    await query.edit_message_text(
        loading_message,
        parse_mode="Markdown"
    )
    
    # Wait a bit to simulate checking
    await asyncio.sleep(2)
    
    # Get stars balance
    stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
    
    if stars_balance and hasattr(stars_balance, 'balance'):
        # Get user_id
        user_id = await UserService.get_or_create_user_id(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get internal stars balance
        internal_stars = await UserService.get_user_stars(user_id)
        
        # Create keyboard for subscription
        keyboard = [
            [InlineKeyboardButton("🔄 Вернуться к выбору плана", callback_data="subscription_menu")],
            [InlineKeyboardButton("🔙 Назад", callback_data="cancel_subscription")]
        ]
        
        # Show balance information
        await query.edit_message_text(
            f"💸 *Баланс звезд* 💸\n\n"
            f"Telegram Stars: *{stars_balance.balance}* звезд\n"
            f"Внутренний баланс: *{internal_stars}* звезд\n\n"
            "Теперь вы можете вернуться к выбору плана подписки.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        # If failed to get balance, show error message
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_stars_purchase")],
            [InlineKeyboardButton("🔙 Назад", callback_data="cancel_subscription")]
        ]
        
        await query.edit_message_text(
            "❌ *Не удалось получить баланс звезд Telegram*\n\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END
