import logging
import traceback
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the application"""
    
    @staticmethod
    async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in telegram handlers"""
        # Log the error
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Log traceback info
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)
        logger.error(f"Traceback: {tb_string}")
        
        # Send a message to the user
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз позже."
            )
    
    @staticmethod
    def handle_telegram_handler_errors(func):
        """Decorator to handle errors in telegram handlers"""
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            try:
                return await func(update, context, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Send a message to the user
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз позже."
                    )
                
                # Re-raise the exception for the global error handler
                raise
        return wrapper
    
    @staticmethod
    def log_exceptions(func):
        """Decorator to log exceptions in any function"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        return wrapper
