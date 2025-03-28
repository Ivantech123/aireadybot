import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, PreCheckoutQueryHandler, MessageHandler, filters
import asyncio
import time
from datetime import datetime

from bot.keyboards.keyboards import get_main_keyboard, get_subscription_plans_keyboard, get_plan_type_keyboard
from bot.services.user_service import UserService
from bot.services.subscription_service import SubscriptionService
from bot.services.payment_service import PaymentService
from bot.services.telegram_stars_service import TelegramStarsService
from bot.utils.config_manager import config
from bot.utils.error_handler import ErrorHandler
from database.models import SubscriptionPlan
from database.db import get_session

# Enable logging
logger = logging.getLogger(__name__)

# Conversation states
SUBSCRIPTION_MENU, SUBSCRIPTION_PLAN_SELECTION, TELEGRAM_STARS_PAYMENT = range(7, 10)

# Subscribe command handler
@ErrorHandler.handle_telegram_handler_errors
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show subscription options"""
    user = update.effective_user
    
    # Get user ID directly
    telegram_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    
    # Get or create user and immediately get user_id
    user_id = await UserService.get_or_create_user_id(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    
    # Store user_id in context to avoid DetachedInstanceError
    context.user_data['user_id'] = user_id
    context.user_data['telegram_id'] = telegram_id
    
    # Get Telegram Stars balance
    stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
    telegram_stars = stars_balance.balance if stars_balance and hasattr(stars_balance, 'balance') else 0
    
    # Get internal stars balance
    internal_stars = await UserService.get_user_stars(user_id)
    
    # Get current user limits - исправлено для предотвращения DetachedInstanceError
    user_limits_dict = await UserService.get_user_limits_as_dict(user_id)
    text_limit = user_limits_dict.get('text_messages_limit', 0)
    image_limit = user_limits_dict.get('image_generations_limit', 0)
    
    # Get free message settings
    from bot.services.admin_service import AdminService
    free_settings = await AdminService.get_free_message_settings()
    
    # Show subscription information
    await update.message.reply_text(
        f"💫 *Подписка на бота* 💫\n\n"
        f"Ваш баланс:\n"
        f"- Telegram Stars: *{telegram_stars}* звезд\n"
        f"- Внутренние звезды: *{internal_stars}* звезд\n\n"
        f"Ваши текущие лимиты:\n"
        f"- Сообщений: *{text_limit}*\n"
        f"- Изображений: *{image_limit}*\n\n"
        f"🎁 *Бесплатные сообщения*:\n"
        f"- Новым пользователям: *{free_settings['initial_free_text']}* сообщений и *{free_settings['initial_free_images']}* изображений\n"
        f"- Ежедневно: *{free_settings['daily_free_messages']}* сообщений\n\n"
        f"Выберите тип подписки:",
        reply_markup=get_subscription_plans_keyboard(None),
        parse_mode="Markdown"
    )
    
    return SUBSCRIPTION_MENU

# Subscription menu handler
@ErrorHandler.handle_telegram_handler_errors
async def subscription_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription menu selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user_id from context to avoid DetachedInstanceError
    user_id = context.user_data.get('user_id')
    telegram_id = context.user_data.get('telegram_id')
    
    # If user_id is not in context, get it from the database
    if not user_id or not telegram_id:
        telegram_id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        
        # Get or create user and immediately get user_id
        user_id = await UserService.get_or_create_user_id(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        # Store user_id in context for future use
        context.user_data['user_id'] = user_id
        context.user_data['telegram_id'] = telegram_id
    
    callback_data = query.data
    
    if callback_data == "cancel_subscription":
        await query.edit_message_text(
            "Подписка отменена.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    if callback_data == "subscription_plans_text":
        # Get text subscription plans
        plans = await SubscriptionService.get_all_subscription_plans('text')
        
        if not plans:
            await query.edit_message_text(
                "Нет доступных планов подписки для чата.",
                reply_markup=None
            )
            return ConversationHandler.END
        
        # Create a new session for working with plan objects
        session = get_session()
        try:
            # Update plan objects in the session
            for plan in plans:
                session.add(plan)
                if not session.is_active:
                    session.refresh(plan)
            
            # Get current user limits
            user_limits_dict = await UserService.get_user_limits_as_dict(user_id)
            text_limit = user_limits_dict.get('text_messages_limit', 0)
            
            # Get active user subscriptions
            active_subs = await SubscriptionService.get_user_active_subscriptions(user_id)
            
            # Update objects in the session and load related objects
            for sub in active_subs:
                session.add(sub)
                # Explicitly load related plan objects
                if not session.is_active:
                    session.refresh(sub)
                # Forcefully load the related plan
                plan = sub.plan
            
            # Now it's safe to access related objects
            active_text_subs = [sub for sub in active_subs if sub.plan.plan_type == 'text']
            
            # Add information about current subscriptions
            current_subs_text = ""
            if active_text_subs:
                current_subs_text = "\n\n🔔 *Ваши активные подписки*:\n"
                for sub in active_text_subs:
                    days_left = (sub.end_date - datetime.utcnow()).days + 1
                    current_subs_text += f"- {sub.plan.name}: ещё {days_left} дней\n"
            
            # Create a keyboard with plans
            keyboard = get_plan_type_keyboard(plans, 'text')
            
            await query.edit_message_text(
                f"📗 *Тарифы для чата*\n\n"
                f"Ваш текущий лимит сообщений: *{text_limit}*\n"
                f"{current_subs_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        finally:
            session.close()
        
        return SUBSCRIPTION_MENU
    
    elif callback_data == "subscription_plans_image":
        # Get image subscription plans
        plans = await SubscriptionService.get_all_subscription_plans('image')
        
        if not plans:
            await query.edit_message_text(
                "Нет доступных планов подписки для изображений.",
                reply_markup=None
            )
            return ConversationHandler.END
        
        # Create a new session for working with plan objects
        session = get_session()
        try:
            # Update plan objects in the session
            for plan in plans:
                session.add(plan)
                if not session.is_active:
                    session.refresh(plan)
            
            # Format plan descriptions
            plans_text = "\n\n".join([f"*{plan.name}* ({plan.stars_cost} ⭐️):\n{plan.description}" for plan in plans])
            
            # Get current user limits
            user_limits_dict = await UserService.get_user_limits_as_dict(user_id)
            image_limit = user_limits_dict.get('image_generations_limit', 0)
            
            # Get active user subscriptions
            active_subs = await SubscriptionService.get_user_active_subscriptions(user_id)
            
            # Update objects in the session and load related objects
            for sub in active_subs:
                session.add(sub)
                # Explicitly load related plan objects
                if not session.is_active:
                    session.refresh(sub)
                # Forcefully load the related plan
                plan = sub.plan
            
            # Now it's safe to access related objects
            active_image_subs = [sub for sub in active_subs if sub.plan.plan_type == 'image']
            
            # Add information about current subscriptions
            current_subs_text = ""
            if active_image_subs:
                current_subs_text = "\n\n🔔 *Ваши активные подписки*:\n"
                for sub in active_image_subs:
                    days_left = (sub.end_date - datetime.utcnow()).days + 1
                    current_subs_text += f"- {sub.plan.name}: ещё {days_left} дней\n"
            
            # Create a keyboard with plans
            keyboard = get_plan_type_keyboard(plans, 'image')
            
            await query.edit_message_text(
                f"🖼 *Тарифы для изображений*\n\n"
                f"Ваш текущий лимит изображений: *{image_limit}*\n"
                f"{current_subs_text}\n"
                f"{plans_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        finally:
            session.close()
        
        return SUBSCRIPTION_MENU
    
    # Default case
    await query.edit_message_text(
        "Неизвестная опция.",
        reply_markup=None
    )
    return ConversationHandler.END

# Subscription plan selection handler
@ErrorHandler.handle_telegram_handler_errors
async def subscription_plan_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription plan selection"""
    query = update.callback_query
    await query.answer()
    
    # Добавляем отладочную логику
    logger = logging.getLogger(__name__)
    logger.info(f"Received callback data: {query.data}")
    
    user = update.effective_user
    
    # Get user_id from context to avoid DetachedInstanceError
    user_id = context.user_data.get('user_id')
    telegram_id = context.user_data.get('telegram_id')
    
    # If user_id is not in context, get it from the database
    if not user_id or not telegram_id:
        telegram_id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        
        # Get or create user and immediately get user_id
        user_id = await UserService.get_or_create_user_id(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        # Store user_id in context for future use
        context.user_data['user_id'] = user_id
        context.user_data['telegram_id'] = telegram_id
    
    callback_data = query.data
    
    if callback_data == "cancel_subscription":
        await query.edit_message_text(
            "Подписка отменена.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    if callback_data == "back_to_subscription_types":
        # Return to subscription types menu
        await query.edit_message_text(
            "Выберите тип подписки:",
            reply_markup=get_subscription_plans_keyboard(None)
        )
        return SUBSCRIPTION_MENU
    
    if callback_data.startswith("subscribe_plan_"):
        plan_id = int(callback_data.split("_")[-1])
        
        # Save plan ID in context for use in payment handler
        context.user_data['selected_plan_id'] = plan_id
        
        # Get plan information
        session = get_session()
        try:
            plan = session.query(SubscriptionPlan).get(plan_id)
            if not plan:
                await query.edit_message_text(
                    "План подписки не найден.",
                    reply_markup=None
                )
                return ConversationHandler.END
                
            # Explicitly load related objects, if any
            if not session.is_active:
                session.refresh(plan)
            
            # Save plan information in context
            context.user_data['plan_cost'] = plan.stars_cost
            context.user_data['plan_name'] = plan.name
            context.user_data['plan_duration'] = plan.duration_days
            context.user_data['plan_limit'] = plan.daily_limit
            
            # Check Telegram Stars balance
            stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
            
            # Form message with plan information
            limit_text = "безлимитные" if plan.daily_limit == -1 else plan.daily_limit
            plan_message = f"🔍 *Подтверждение подписки* 🔍\n\n"
            plan_message += f"План: *{plan.name}*\n"
            plan_message += f"Тип: *{plan.plan_type}*\n"
            plan_message += f"Стоимость: *{plan.stars_cost}* звезд\n"
            plan_message += f"Срок действия: *{plan.duration_days}* дней\n"
            plan_message += f"Ежедневный лимит: *{limit_text}* сообщений\n\n"
            
            # Add information about Telegram Stars balance
            if stars_balance and hasattr(stars_balance, 'balance'):
                plan_message += f"Ваш текущий баланс: *{stars_balance.balance}* звезд\n"
                
                # Check if there are enough stars for subscription
                if stars_balance.balance >= plan.stars_cost:
                    plan_message += f"У вас достаточно звезд для оформления подписки!\n"
                    
                    # Create keyboard with confirmation button
                    keyboard = [
                        [InlineKeyboardButton("Подтвердить оплату", callback_data="confirm_telegram_stars_payment")],
                        [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                        [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                    ]
                else:
                    # If not enough stars, offer to buy
                    plan_message += f"Недостаточно звезд для оформления подписки.\n"
                    plan_message += f"Необходимо еще: *{plan.stars_cost - stars_balance.balance}* звезд.\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("Купить звёзды Telegram", url="https://t.me/stars/buy")],
                        [InlineKeyboardButton("Проверить баланс", callback_data="check_stars_purchase")],
                        [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                        [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                    ]
            else:
                # If unable to get Telegram Stars balance
                plan_message += "Не удалось проверить баланс звезд Telegram.\n"
                plan_message += "Возможно, у вас нет доступа к Telegram Stars или произошла ошибка.\n"
                
                keyboard = [
                    [InlineKeyboardButton("Купить звёзды Telegram", url="https://t.me/stars/buy")],
                    [InlineKeyboardButton("Проверить баланс", callback_data="check_stars_purchase")],
                    [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                    [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                ]
            
            await query.edit_message_text(
                plan_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return SUBSCRIPTION_PLAN_SELECTION
        finally:
            session.close()

# Telegram Stars payment handler
@ErrorHandler.handle_telegram_handler_errors
async def telegram_stars_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Telegram Stars payment for subscription"""
    query = update.callback_query
    await query.answer()
    
    # Добавляем отладочную логику
    logger = logging.getLogger(__name__)
    logger.info(f"Telegram Stars payment handler received callback data: {query.data}")
    
    user = update.effective_user
    telegram_id = user.id
    
    # Get user_id from context
    user_id = context.user_data.get('user_id')
    if not user_id:
        # Get user_id from database if not in context
        user_id = await UserService.get_or_create_user_id(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        context.user_data['user_id'] = user_id
    
    # Get plan information from context
    plan_id = context.user_data.get('selected_plan_id')
    plan_name = context.user_data.get('plan_name')
    plan_cost = context.user_data.get('plan_cost')
    
    if not plan_id or not plan_name or not plan_cost:
        await query.edit_message_text(
            "Ошибка: Информация о плане подписки не найдена.",
            reply_markup=None
        )
        return ConversationHandler.END
    
    # Check if this is a balance check or payment confirmation
    if query.data == "check_stars_purchase":
        # Just check the balance and update the message
        stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
        
        if stars_balance and hasattr(stars_balance, 'balance'):
            # Get plan information from database to ensure it's up to date
            session = get_session()
            try:
                plan = session.query(SubscriptionPlan).get(plan_id)
                if not plan:
                    await query.edit_message_text(
                        "План подписки не найден.",
                        reply_markup=None
                    )
                    return ConversationHandler.END
                
                # Update message with current balance
                limit_text = "безлимитные" if plan.daily_limit == -1 else plan.daily_limit
                plan_message = f"🔍 *Подтверждение подписки* 🔍\n\n"
                plan_message += f"План: *{plan.name}*\n"
                plan_message += f"Тип: *{plan.plan_type}*\n"
                plan_message += f"Стоимость: *{plan.stars_cost}* звезд\n"
                plan_message += f"Срок действия: *{plan.duration_days}* дней\n"
                plan_message += f"Ежедневный лимит: *{limit_text}* сообщений\n\n"
                plan_message += f"Ваш текущий баланс: *{stars_balance.balance}* звезд\n"
                
                # Check if there are enough stars for subscription
                if stars_balance.balance >= plan.stars_cost:
                    plan_message += f"У вас достаточно звезд для оформления подписки!\n"
                    
                    # Create keyboard with confirmation button
                    keyboard = [
                        [InlineKeyboardButton("Подтвердить оплату", callback_data="confirm_telegram_stars_payment")],
                        [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                        [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                    ]
                else:
                    # If not enough stars, offer to buy
                    plan_message += f"Недостаточно звезд для оформления подписки.\n"
                    plan_message += f"Необходимо еще: *{plan.stars_cost - stars_balance.balance}* звезд.\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("Купить звёзды Telegram", url="https://t.me/stars/buy")],
                        [InlineKeyboardButton("Проверить баланс", callback_data="check_stars_purchase")],
                        [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                        [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                    ]
                
                await query.edit_message_text(
                    plan_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            finally:
                session.close()
        else:
            # If unable to get Telegram Stars balance
            await query.edit_message_text(
                "Не удалось проверить баланс звезд Telegram.\n"
                "Возможно, у вас нет доступа к Telegram Stars или произошла ошибка.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Купить звёзды Telegram", url="https://t.me/stars/buy")],
                    [InlineKeyboardButton("Проверить баланс", callback_data="check_stars_purchase")],
                    [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                    [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
                ])
            )
        
        return SUBSCRIPTION_PLAN_SELECTION
    
    # This is a payment confirmation
    # Show loading message
    await query.edit_message_text(
        "Обрабатываем вашу подписку...",
        reply_markup=None
    )
    
    # Process payment with Telegram Stars
    result = await SubscriptionService.process_telegram_stars_payment(
        user_id=user_id,
        telegram_id=telegram_id,
        plan_id=plan_id,
        stars_amount=plan_cost
    )
    
    if result[0]:  # Success
        # Show success message
        await query.edit_message_text(
            f"{result[1]}\n\n"
            f"Теперь вы можете использовать расширенные возможности бота!\n"
            f"Проверить свои текущие лимиты можно командой /limits",
            reply_markup=None
        )
    else:  # Error
        # Show error message
        await query.edit_message_text(
            f"{result[1]}\n\n"
            f"Пожалуйста, попробуйте еще раз позже или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="back_to_subscription_types")],
                [InlineKeyboardButton("Отмена", callback_data="cancel_subscription")]
            ])
        )
    
    return ConversationHandler.END

# Get all handlers
def get_subscription_handlers():
    """Return all subscription handlers"""
    return [
        CommandHandler("subscribe", subscribe_command),
        CallbackQueryHandler(subscription_menu_handler, pattern=r"^subscription_menu$"),
        CallbackQueryHandler(subscription_menu_handler, pattern=r"^subscription_plans_text$"),
        CallbackQueryHandler(subscription_menu_handler, pattern=r"^subscription_plans_image$"),
        CallbackQueryHandler(subscription_plan_selection_handler, pattern=r"^subscribe_plan_\d+$"),
        CallbackQueryHandler(subscription_plan_selection_handler, pattern=r"^back_to_subscription_types$"),
        CallbackQueryHandler(subscription_plan_selection_handler, pattern=r"^cancel_subscription$"),
        CallbackQueryHandler(telegram_stars_payment_handler, pattern=r"^confirm_telegram_stars_payment$"),
        CallbackQueryHandler(telegram_stars_payment_handler, pattern=r"^check_stars_purchase$"),
        CallbackQueryHandler(subscription_plan_selection_handler, pattern=r"^buy_stars$"),
        CallbackQueryHandler(subscription_plan_selection_handler, pattern=r"^buy_internal_stars$"),
    ]
