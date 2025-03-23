import os
import logging
import asyncio
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes, PreCheckoutQueryHandler
from dotenv import load_dotenv

# Import utilities
from bot.utils.config_manager import config
from bot.utils.error_handler import ErrorHandler

# Load environment variables
load_dotenv()

# Import handlers
from bot.handlers.basic_handlers import (
    start, help_command, admin_command, admin_auth, 
    limits_command, invite_command, copy_referral_link,
    ADMIN_AUTH, ADMIN_MENU, cancel, cancel_callback
)

from bot.handlers.admin_handlers import (
    admin_menu, broadcast_message, broadcast_confirm, edit_ad, manage_users, user_management_actions,
    BROADCAST_MESSAGE, EDIT_AD, MANAGE_USERS, FREE_LIMITS_SETTINGS, FREE_LIMITS_UPDATE, free_limits_settings_handler, update_free_limits_handler
)
from bot.handlers.chat_handlers import (
    text_question_start, text_question_process, voice_question_start, voice_question_process,
    TEXT_QUESTION, VOICE_QUESTION
)
from bot.handlers.image_handlers import (
    image_generation_start, image_generation_process,
    IMAGE_GENERATION
)
from bot.handlers.subscription_handlers import (
    subscribe_command, subscription_menu_handler, subscription_plan_selection_handler,
    SUBSCRIPTION_MENU, SUBSCRIPTION_PLAN_SELECTION
)
from bot.handlers.telegram_stars_handlers import (
    telegram_stars_command, telegram_stars_menu_handler, precheckout_callback, successful_payment_callback, create_stars_invoice,
    TELEGRAM_STARS_MENU
)
from database.db import init_db

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("error.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set up proper event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def startup_tasks():
    """Perform startup tasks like database initialization"""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.error(traceback.format_exc())
        return False


def main():
    """Main function to run the bot"""
    try:
        # Initialize database asynchronously
        loop = asyncio.get_event_loop()
        db_init_success = loop.run_until_complete(startup_tasks())
        
        if not db_init_success:
            logger.error("Failed to initialize database. Exiting...")
            return
        
        # Get token from environment variables
        token = config.get('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("No token provided. Please set TELEGRAM_BOT_TOKEN environment variable.")
            return
        
        # Log startup information
        logger.info(f"Starting bot with API credentials:")
        logger.info(f"API ID: {config.get('TELEGRAM_API_ID')}")
        logger.info(f"Using Telegram Stars: {config.get('USE_TELEGRAM_STARS', 'True')}")
        
        # Create the Application
        application = Application.builder().token(token).build()
        
        # Register error handler
        application.add_error_handler(ErrorHandler.handle_error)
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("limits", limits_command))
        application.add_handler(CommandHandler("invite", invite_command))
        application.add_handler(CommandHandler("telegram_stars", telegram_stars_command))
        application.add_handler(CommandHandler("stars", telegram_stars_command))
        application.add_handler(CommandHandler("admin", admin_command))
        
        # Text question conversation handler
        text_question_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^📝 Задать вопрос$"), text_question_start)],
            states={
                TEXT_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_question_process)],
            },
            fallbacks=[MessageHandler(filters.Regex(r"^❌ Отмена$"), cancel)],
        )
        application.add_handler(text_question_conv_handler)
        
        # Voice question conversation handler
        voice_question_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^🎙 Голосовой вопрос$"), voice_question_start)],
            states={
                VOICE_QUESTION: [MessageHandler(filters.VOICE, voice_question_process)],
            },
            fallbacks=[MessageHandler(filters.Regex(r"^❌ Отмена$"), cancel)],
        )
        application.add_handler(voice_question_conv_handler)
        
        # Image generation conversation handler
        image_generation_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(r"^🖼 Генерация картинки$"), image_generation_start)],
            states={
                IMAGE_GENERATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, image_generation_process)],
            },
            fallbacks=[MessageHandler(filters.Regex(r"^❌ Отмена$"), cancel)],
        )
        application.add_handler(image_generation_conv_handler)
        
        # Admin conversation handler
        admin_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("admin", admin_command)],
            states={
                ADMIN_AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_auth)],
                ADMIN_MENU: [
                    CallbackQueryHandler(admin_menu),
                    MessageHandler(filters.Regex(r"^🔙 Назад$"), cancel),
                ],
                BROADCAST_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔙 Назад$"), broadcast_message),
                    MessageHandler(filters.Regex(r"^🔙 Назад$"), cancel),
                ],
                EDIT_AD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔙 Назад$"), edit_ad),
                    MessageHandler(filters.Regex(r"^🔙 Назад$"), cancel),
                ],
                MANAGE_USERS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔙 Назад$"), manage_users),
                    MessageHandler(filters.Regex(r"^🔙 Назад$"), cancel),
                ],
                FREE_LIMITS_SETTINGS: [
                    CallbackQueryHandler(free_limits_settings_handler),
                ],
                FREE_LIMITS_UPDATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, update_free_limits_handler),
                    CallbackQueryHandler(free_limits_settings_handler),
                ],
            },
            fallbacks=[MessageHandler(filters.Regex(r"^❌ Отмена$"), cancel)],
        )
        application.add_handler(admin_conv_handler)
        
        # Add callback query handler for broadcast confirmation
        application.add_handler(CallbackQueryHandler(broadcast_confirm, pattern=r"^(confirm|cancel)_broadcast$"))
        
        # Add callback query handler for user management actions
        application.add_handler(CallbackQueryHandler(user_management_actions, pattern=r"^(add_stars_|reset_limits_)\d+$"))
        
        # Add callback query handler for star purchase
        application.add_handler(CallbackQueryHandler(create_stars_invoice, pattern=r"^buy_package_\d+$"))
        
        # Add callback query handler for buying stars menu
        application.add_handler(CallbackQueryHandler(create_stars_invoice, pattern=r"^buy_stars$"))
        
        # Add callback query handler for canceling subscription
        application.add_handler(CallbackQueryHandler(cancel_callback, pattern=r"^cancel_subscription$"))
        
        # Subscription conversation handler
        subscription_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("subscribe", subscribe_command), MessageHandler(filters.Regex(r"^⭐️ Подписка$"), subscribe_command)],
            states={
                SUBSCRIPTION_MENU: [CallbackQueryHandler(subscription_menu_handler)],
                SUBSCRIPTION_PLAN_SELECTION: [CallbackQueryHandler(subscription_plan_selection_handler)],
            },
            fallbacks=[CallbackQueryHandler(cancel_callback, pattern=r"^cancel_")],
        )
        application.add_handler(subscription_conv_handler)
        
        # Add handlers for main menu buttons that are not part of conversation handlers
        application.add_handler(MessageHandler(filters.Regex(r"^📊 Мои лимиты$"), limits_command))
        application.add_handler(MessageHandler(filters.Regex(r"^👥 Пригласить друга$"), invite_command))
        
        # Add callback query handler for referral link copying
        application.add_handler(CallbackQueryHandler(copy_referral_link, pattern=r"^copy_referral_"))
        
        # Add callback query handler for Telegram Stars menu
        application.add_handler(CallbackQueryHandler(telegram_stars_menu_handler, pattern=r"^(buy_telegram_stars|check_telegram_stars_balance|back_to_stars_menu|topup_stars_\d+_.+_.+)$"))
        
        # Add handlers for Telegram Stars payments
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
        
        # Add handler for checking stars purchase
        application.add_handler(CallbackQueryHandler(create_stars_invoice, pattern="^check_stars_purchase$"))
        
        # Telegram Stars conversation handler
        telegram_stars_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("stars", telegram_stars_command)],
            states={
                TELEGRAM_STARS_MENU: [
                    CallbackQueryHandler(telegram_stars_menu_handler, pattern=r"^(buy_telegram_stars|check_telegram_stars_balance|back_to_stars_menu|topup_stars_\d+_.+_.+)$")
                ],
            },
            fallbacks=[CallbackQueryHandler(cancel_callback, pattern=r"^cancel$")],
            per_message=False
        )
        application.add_handler(telegram_stars_conv_handler)
        
        # Set up scheduler for daily free message reset
        from bot.services.user_service import UserService
        from datetime import time
        
        # Add task for daily free message reset at 00:00
        application.job_queue.run_daily(lambda context: asyncio.create_task(UserService.reset_daily_free_messages()), time=time(0, 0))
        
        # Log startup information
        logger.info("Bot started successfully")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Critical error in main function: {e}")
        logger.critical(traceback.format_exc())

if __name__ == '__main__':
    main()
