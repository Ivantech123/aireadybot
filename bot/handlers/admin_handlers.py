import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from bot.keyboards.keyboards import get_main_keyboard, get_admin_keyboard, get_back_keyboard
from bot.services.admin_service import AdminService
from bot.services.user_service import UserService
from config.config import ADMIN_USER_ID

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
ADMIN_MENU, BROADCAST_MESSAGE, BROADCAST_CONFIRM, EDIT_AD, MANAGE_USERS, FREE_LIMITS_SETTINGS, FREE_LIMITS_UPDATE = range(3, 10)

# Admin menu handler
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin menu options"""
    query = update.callback_query
    
    if query:
        await query.answer()
        callback_data = query.data
        
        if callback_data == "admin_broadcast":
            await query.edit_message_text(
                "📣 Введите сообщение для рассылки всем пользователям:",
                reply_markup=get_back_keyboard()
            )
            return BROADCAST_MESSAGE
        
        elif callback_data == "admin_edit_ad":
            # Get current advertisement
            ad_text = await AdminService.get_advertisement()
            
            await query.edit_message_text(
                f"📝 Текущий рекламный текст:\n\n{ad_text or 'Нет рекламного текста'}\n\nВведите новый рекламный текст:",
                reply_markup=get_back_keyboard()
            )
            return EDIT_AD
        
        elif callback_data == "admin_manage_users":
            await query.edit_message_text(
                "👥 Введите Telegram ID пользователя для управления:",
                reply_markup=get_back_keyboard()
            )
            return MANAGE_USERS
            
        elif callback_data == "admin_free_limits":
            # Получаем текущие настройки бесплатных лимитов
            from bot.services.admin_service import AdminService
            settings = await AdminService.get_free_message_settings()
            
            await query.edit_message_text(
                f"🎁 Настройки бесплатных лимитов:\n\n"
                f"📝 Начальные бесплатные сообщения: {settings['initial_free_text']}\n"
                f"🖼 Начальные бесплатные изображения: {settings['initial_free_images']}\n"
                f"🔄 Ежедневные бесплатные сообщения: {settings['daily_free_messages']}\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Изменить настройки", callback_data="edit_free_limits")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
                ])
            )
            return FREE_LIMITS_SETTINGS
        
        elif callback_data == "admin_back":
            await query.edit_message_text(
                "🔙 Вернуться в главное меню.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    return ADMIN_MENU

# Broadcast message handler
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle broadcast message input"""
    message_text = update.message.text
    
    if message_text == "🔙 Назад":
        await update.message.reply_text(
            "🛠 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU
    
    # Store message text in context
    context.user_data['broadcast_message'] = message_text
    
    # Create confirm keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_broadcast")]
    ]
    
    await update.message.reply_text(
        f"📣 Вы собираетесь отправить следующее сообщение всем пользователям:\n\n{message_text}\n\nПодтвердите отправку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return BROADCAST_CONFIRM

# Broadcast confirm handler
async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle broadcast confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_broadcast":
        # Get message from context
        message_text = context.user_data.get('broadcast_message', '')
        
        if not message_text:
            await query.edit_message_text(
                "❌ Ошибка: сообщение не найдено.",
                reply_markup=None
            )
            return ADMIN_MENU
        
        # Send broadcast message
        success, count = await AdminService.send_broadcast_message(message_text, context.bot)
        
        if success:
            await query.edit_message_text(
                f"✅ Сообщение успешно отправлено {count} пользователям.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при отправке сообщения.",
                reply_markup=None
            )
        
        # Clear context
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
        
        # Return to admin menu
        await query.message.reply_text(
            "🛠 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU
    
    elif query.data == "cancel_broadcast":
        # Clear context
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
        
        await query.edit_message_text(
            "❌ Рассылка отменена.",
            reply_markup=None
        )
        
        # Return to admin menu
        await query.message.reply_text(
            "🛠 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU

# Edit advertisement handler
async def edit_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle advertisement edit"""
    ad_text = update.message.text
    
    if ad_text == "🔙 Назад":
        await update.message.reply_text(
            "🛠 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU
    
    # Update advertisement
    success = await AdminService.update_advertisement(ad_text)
    
    if success:
        await update.message.reply_text(
            "✅ Рекламный текст успешно обновлен.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при обновлении рекламного текста.",
            reply_markup=get_admin_keyboard()
        )
    
    return ADMIN_MENU

# Manage users handler
async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user management"""
    user_id_text = update.message.text
    
    if user_id_text == "🔙 Назад":
        await update.message.reply_text(
            "🛠 Админ-панель",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU
    
    try:
        telegram_id = int(user_id_text)
        
        # Get user info using the new method that doesn't return detached objects
        user_info = await UserService.get_user_info_by_telegram_id(telegram_id)
        
        if not user_info:
            await update.message.reply_text(
                "❌ Пользователь не найден.",
                reply_markup=get_admin_keyboard()
            )
            return ADMIN_MENU
        
        # Get user limits
        user_limits = await UserService.get_user_limits(user_info['id'])
        
        # Get user stars
        stars = await UserService.get_user_stars(user_info['id'])
        
        # Create user management keyboard
        from bot.keyboards.keyboards import get_user_management_keyboard_admin
        keyboard = get_user_management_keyboard_admin(user_info['id'])
        
        await update.message.reply_text(
            f"👤 Информация о пользователе:\n\n"
            f"ID: {user_info['id']}\n"
            f"Telegram ID: {user_info['telegram_id']}\n"
            f"Имя: {user_info['first_name']} {user_info['last_name'] or ''}\n"
            f"Username: {user_info['username'] or 'Не указан'}\n"
            f"Звёзды: {stars}\n\n"
            f"Лимиты:\n"
            f"Текстовые сообщения: {user_limits.text_messages_used}/{user_limits.text_messages_limit}\n"
            f"Голосовые сообщения: {user_limits.voice_messages_used}/{user_limits.voice_messages_limit}\n"
            f"Генерация изображений: {user_limits.image_generations_used}/{user_limits.image_generations_limit}\n\n"
            f"Выберите действие:",
            reply_markup=keyboard
        )
        
        return ADMIN_MENU
    
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ID. Пожалуйста, введите числовой ID.",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU

# User management actions handler
async def user_management_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user management actions"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("add_stars_"):
        user_id = int(callback_data.split("_")[-1])
        
        # Add 50 stars to user
        success = await UserService.add_stars(user_id, 50)
        
        if success:
            # Get updated stars
            stars = await UserService.get_user_stars(user_id)
            
            await query.edit_message_text(
                f"✅ Добавлено 50 звёзд пользователю. Текущий баланс: {stars} звёзд.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при добавлении звёзд.",
                reply_markup=None
            )
    
    elif callback_data.startswith("reset_limits_"):
        user_id = int(callback_data.split("_")[-1])
        
        # Reset user limits
        success = await UserService.reset_user_limits(user_id)
        
        if success:
            await query.edit_message_text(
                "✅ Лимиты пользователя сброшены.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при сбросе лимитов.",
                reply_markup=None
            )
    
    # Return to admin menu
    await query.message.reply_text(
        "🛠 Админ-панель",
        reply_markup=get_admin_keyboard()
    )
    return ADMIN_MENU

# Обработчик редактирования настроек бесплатных лимитов
async def free_limits_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free limits settings"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_free_limits":
        await query.edit_message_text(
            "🔄 Введите новые настройки бесплатных лимитов в формате:\n\n"
            "<начальные_сообщения>,<начальные_изображения>,<ежедневные_сообщения>\n\n"
            "Например: 5,3,1",
            reply_markup=get_back_keyboard()
        )
        return FREE_LIMITS_UPDATE
    
    elif query.data == "admin_back":
        await query.edit_message_text(
            "👨‍💼 Панель администратора",
            reply_markup=get_admin_keyboard()
        )
        return ADMIN_MENU

# Обработчик обновления настроек бесплатных лимитов
async def update_free_limits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle updating free limits settings"""
    message = update.message.text.strip()
    
    try:
        # Парсим введенные значения
        values = message.split(',')
        if len(values) != 3:
            raise ValueError("Неверный формат")
            
        initial_text = int(values[0])
        initial_images = int(values[1])
        daily_messages = int(values[2])
        
        # Проверяем, что значения положительные
        if initial_text < 0 or initial_images < 0 or daily_messages < 0:
            raise ValueError("Значения должны быть положительными")
        
        # Обновляем настройки
        from bot.services.admin_service import AdminService
        success = await AdminService.update_free_message_settings(
            initial_text, initial_images, daily_messages
        )
        
        if success:
            await update.message.reply_text(
                "✅ Настройки бесплатных лимитов успешно обновлены!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Вернуться в админ-панель", callback_data="admin_back")]
                ])
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при обновлении настроек.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data="edit_free_limits")],
                    [InlineKeyboardButton("🔙 Вернуться в админ-панель", callback_data="admin_back")]
                ])
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}\n\nВведите настройки в формате: <начальные_сообщения>,<начальные_изображения>,<ежедневные_сообщения>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="edit_free_limits")],
                [InlineKeyboardButton("🔙 Вернуться в админ-панель", callback_data="admin_back")]
            ])
        )
    
    return FREE_LIMITS_SETTINGS

# Check if user is admin
async def is_admin(update: Update) -> bool:
    """Check if the user is an admin"""
    user = update.effective_user
    return user.id == ADMIN_USER_ID
