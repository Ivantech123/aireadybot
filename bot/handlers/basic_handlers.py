from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
import os
import uuid
import logging
from datetime import datetime, timedelta

from bot.keyboards.keyboards import get_main_keyboard, get_cancel_keyboard, get_back_keyboard
from bot.services.user_service import UserService
from bot.services.admin_service import AdminService
from bot.services.openai_service import OpenAIService
from config.config import ADMIN_USERNAME, ADMIN_PASSWORD

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
TEXT_QUESTION, VOICE_QUESTION, IMAGE_GENERATION = range(3)
ADMIN_AUTH, ADMIN_MENU = range(3, 5)
BROADCAST_MESSAGE, BROADCAST_CONFIRM = range(5, 7)
SUBSCRIPTION_MENU, SUBSCRIPTION_PLAN_SELECTION = range(7, 9)

# OpenAI service instance
openai_service = OpenAIService()

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
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
    
    # Process referral if provided
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
        await UserService.process_referral(user_id, referral_code)
    
    # Send welcome message with main keyboard
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот с искусственным интеллектом, который поможет ответить на ваши вопросы.",
        reply_markup=get_main_keyboard()
    )

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Справка по командам:\n\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n"
        "/limits - Проверить ваши лимиты\n"
        "/subscribe - Подписка на тарифы\n"
        "/invite - Пригласить друга\n"
        "/admin - Войти в админ-панель (только для администраторов)\n\n"
        "Вы также можете использовать кнопки меню для навигации.",
        reply_markup=get_main_keyboard()
    )

# Admin command handler
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin authentication"""
    await update.message.reply_text(
        "Пожалуйста, введите имя пользователя и пароль в формате:\n\nusername password",
        reply_markup=get_cancel_keyboard()
    )
    return ADMIN_AUTH

# Admin authentication handler
async def admin_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify admin credentials"""
    text = update.message.text
    parts = text.split()
    
    if len(parts) == 2 and parts[0] == ADMIN_USERNAME and parts[1] == ADMIN_PASSWORD:
        from bot.keyboards.keyboards import get_admin_keyboard
        await update.message.reply_text(
            "Авторизация успешна! Добро пожаловать в админ-панель.",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU
    else:
        await update.message.reply_text(
            "Неверное имя пользователя или пароль. Попробуйте еще раз или нажмите 'Отмена'.",
            reply_markup=get_cancel_keyboard()
        )
        return ADMIN_AUTH

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation and return to main menu"""
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Cancel callback handler
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation and return to main menu (for callback queries)"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Операция отменена.",
        reply_markup=None
    )
    await query.message.reply_text(
        "Вернулись в главное меню.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Back to main menu handler
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to main menu"""
    await update.message.reply_text(
        "Вернулись в главное меню.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# Check limits command handler
async def limits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user limits"""
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
    
    # Get user limits
    user_limits = await UserService.get_user_limits(user_id)
    
    # Get user stars
    stars = await UserService.get_user_stars(user_id)
    
    # Get user subscriptions
    from bot.services.subscription_service import SubscriptionService
    text_subscriptions = await SubscriptionService.get_user_active_subscriptions(user_id, 'text')
    image_subscriptions = await SubscriptionService.get_user_active_subscriptions(user_id, 'image')
    
    # Создаем сессию для работы с объектами
    from database.db import get_session
    session = get_session()
    try:
        # Обновляем объекты в сессии и загружаем связанные объекты
        for sub in text_subscriptions:
            session.add(sub)
            # Явно загружаем связанные объекты plan
            if not session.is_active:
                session.refresh(sub)
            # Принудительно загружаем связанный план
            plan = sub.plan
        
        for sub in image_subscriptions:
            session.add(sub)
            # Явно загружаем связанные объекты plan
            if not session.is_active:
                session.refresh(sub)
            # Принудительно загружаем связанный план
            plan = sub.plan
        
        # Format subscription text
        text_sub_info = "\n".join([f"- {sub.plan.name} (до {sub.end_date.strftime('%d.%m.%Y')})" for sub in text_subscriptions]) if text_subscriptions else "Нет активных подписок"
        image_sub_info = "\n".join([f"- {sub.plan.name} (до {sub.end_date.strftime('%d.%m.%Y')})" for sub in image_subscriptions]) if image_subscriptions else "Нет активных подписок"
        
        await update.message.reply_text(
            f"Ваши текущие лимиты:\n\n"
            f"Звёзды: {stars}\n\n"
            f"Текстовые сообщения: {user_limits.text_messages_used}/{user_limits.text_messages_limit} сегодня\n"
            f"Голосовые сообщения: {user_limits.voice_messages_used}/{user_limits.voice_messages_limit} сегодня\n"
            f"Генерация картинок: {user_limits.image_generations_used}/{user_limits.image_generations_limit} сегодня\n\n"
            f"Подписки на чат:\n{text_sub_info}\n\n"
            f"Подписки на картинки:\n{image_sub_info}\n\n"
            f"Лимиты обновляются ежедневно в 00:00 UTC.",
            reply_markup=get_main_keyboard()
        )
    finally:
        session.close()

# Invite command handler
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and show referral link"""
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
    
    # Get referral code
    referral_code = await UserService.get_user_referral_code(user_id)
    
    # Get bot info
    bot = context.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    # Generate referral link
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    # Create referral keyboard
    from bot.keyboards.keyboards import get_referral_keyboard
    keyboard = get_referral_keyboard(bot_username, referral_code)
    
    await update.message.reply_text(
        f"Пригласите друзей и получите бонус!\n\n"
        f"За каждого приглашенного друга вы и ваш друг получите по 10 звёзд.\n\n"
        f"Ваша реферальная ссылка:\n{referral_link}",
        reply_markup=keyboard
    )

# Copy referral link handler
async def copy_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle referral link copy button"""
    query = update.callback_query
    await query.answer("Ссылка скопирована в буфер обмена")
    
    # Extract referral code from callback data
    referral_code = query.data.split('_')[2]
    
    # Get bot info
    bot = context.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    # Generate referral link
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    # Send as a separate message for easier copying
    await query.message.reply_text(
        f"{referral_link}"
    )
