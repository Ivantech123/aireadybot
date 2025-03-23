from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Main menu keyboard
def get_main_keyboard():
    keyboard = [
        ["📝 Задать вопрос", "🎙 Голосовой вопрос"],
        ["🖼 Генерация картинки", "⭐️ Подписка"],
        ["📊 Мои лимиты", "👥 Пригласить друга"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Cancel keyboard
def get_cancel_keyboard():
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Back to main menu keyboard
def get_back_keyboard():
    keyboard = [["🔙 Вернуться в главное меню"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Subscription packages keyboard
def get_subscription_keyboard(packages):
    keyboard = []
    for package in packages:
        keyboard.append([
            InlineKeyboardButton(
                f"{package.name} - {package.stars_amount} ⭐️ за {package.price} руб.", 
                callback_data=f"buy_package_{package.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("Отменить", callback_data="cancel_subscription")])
    return InlineKeyboardMarkup(keyboard)

# Subscription plans keyboard
def get_subscription_plans_keyboard(plan_type):
    keyboard = [
        [InlineKeyboardButton("📝 Тарифы для чата", callback_data="subscription_plans_text")],
        [InlineKeyboardButton("🖼 Тарифы для картинок", callback_data="subscription_plans_image")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Specific subscription plan type keyboard
def get_plan_type_keyboard(plans, plan_type):
    keyboard = []
    for plan in plans:
        # Добавляем более подробную информацию о тарифе
        if plan.daily_limit == -1:
            limit_text = "Безлимит"
        else:
            limit_text = f"{plan.daily_limit}/день"
            
        keyboard.append([
            InlineKeyboardButton(
                f"{plan.name} - {plan.stars_cost} ⭐️ ({limit_text}, {plan.duration_days} дней)", 
                callback_data=f"subscribe_plan_{plan.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_subscription_types")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription")])
    return InlineKeyboardMarkup(keyboard)

# Admin keyboard
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Отправить сообщение", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📝 Редактировать рекламу", callback_data="admin_edit_ad")],
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_manage_users")],
        [InlineKeyboardButton("🎁 Настройки бесплатных лимитов", callback_data="admin_free_limits")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Admin broadcast confirmation keyboard
def get_broadcast_confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("✔️ Подтвердить", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Admin user management keyboard
def get_user_management_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить звезды", callback_data=f"add_stars_{user_id}")],
        [InlineKeyboardButton("🚫 Заблокировать/Разблокировать", callback_data=f"toggle_block_{user_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

# User management keyboard
def get_user_management_keyboard_admin(user_id):
    """Get keyboard for user management"""
    keyboard = [
        [InlineKeyboardButton("⭐️ Добавить 50 звезд", callback_data=f"add_stars_{user_id}")],
        [InlineKeyboardButton("📈 Сбросить лимиты", callback_data=f"reset_limits_{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Referral keyboard
def get_referral_keyboard(bot_username, referral_code):
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    keyboard = [
        [InlineKeyboardButton("📋 Скопировать ссылку", callback_data=f"copy_referral_{referral_code}")],
        [InlineKeyboardButton("📱 Поделиться", url=f"https://t.me/share/url?url={referral_link}&text=Пробуй этот крутой бота с ChatGPT!")]
    ]
    return InlineKeyboardMarkup(keyboard)
