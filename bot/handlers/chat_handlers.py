import os
import tempfile
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from bot.services.user_service import UserService
from bot.services.admin_service import AdminService
from bot.services.openai_service import OpenAIService
from bot.services.payment_service import PaymentService
from bot.utils.config_manager import config
from bot.utils.error_handler import ErrorHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
TEXT_QUESTION, VOICE_QUESTION = range(2)

# OpenAI service instance
openai_service = OpenAIService()

# Get message costs from config
TEXT_MESSAGE_STARS_COST = int(config.get('TEXT_MESSAGE_STARS_COST', 1))
VOICE_MESSAGE_STARS_COST = int(config.get('VOICE_MESSAGE_STARS_COST', 2))

# Text question handler - entry point
@ErrorHandler.handle_telegram_handler_errors
async def text_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the text question conversation"""
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
    
    # Check if user has reached their limits
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'text')
    
    if not has_free_limit:
        # Check if user has enough stars
        has_stars, stars_count, cost = await PaymentService.check_stars_for_service(user_id, 'text')
        
        if not has_stars:
            await update.message.reply_text(
                f"❌ Вы достигли лимита бесплатных текстовых сообщений на сегодня.\n\n"
                f"Для продолжения вам необходимо приобрести звёзды или подписку.\n\n"
                f"У вас {stars_count} звёзд, а требуется {TEXT_MESSAGE_STARS_COST} звёзд за одно сообщение.\n\n"
                f"Используйте команду /subscribe для покупки подписки или звёзд.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "Введите ваш вопрос:",
        reply_markup=get_cancel_keyboard()
    )
    
    return TEXT_QUESTION

# Text question handler - process question
@ErrorHandler.handle_telegram_handler_errors
async def text_question_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the text question"""
    user = update.effective_user
    question = update.message.text
    
    # Get user_id from context to avoid DetachedInstanceError
    user_id = context.user_data.get('user_id')
    
    # If user_id is not in context, get it from the database
    if not user_id:
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
    
    # Check if user has reached their limits
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'text')
    
    if not has_free_limit:
        # Try to use stars
        success, message = await PaymentService.use_stars_for_service(user_id, 'text')
        if not success:
            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    try:
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Generate response using OpenAI
        logger.info(f"Processing text question: {question}")
        response, tokens = await openai_service.generate_text_response(question)
        
        # Get advertisement
        ad_text = await AdminService.get_advertisement()
        ad_footer = f"\n\n---\n{ad_text}" if ad_text else ""
        
        # Send response
        await update.message.reply_text(
            f"{response}{ad_footer}",
            reply_markup=get_main_keyboard()
        )
        
        # Update user usage
        await UserService.update_user_usage(user_id, 'text')
        
        # Log message
        await UserService.log_message(user_id, 'text', question, response, tokens)
        
    except Exception as e:
        logger.error(f"Error processing text question: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

# Voice question handler - entry point
@ErrorHandler.handle_telegram_handler_errors
async def voice_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the voice question conversation"""
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
    
    # Check if user has reached their limits
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'voice')
    
    if not has_free_limit:
        # Check if user has enough stars
        has_stars, stars_count, cost = await PaymentService.check_stars_for_service(user_id, 'voice')
        
        if not has_stars:
            await update.message.reply_text(
                f"❌ Вы достигли лимита бесплатных голосовых сообщений на сегодня.\n\n"
                f"Для продолжения вам необходимо приобрести звёзды или подписку.\n\n"
                f"У вас {stars_count} звёзд, а требуется {VOICE_MESSAGE_STARS_COST} звёзд за одно сообщение.\n\n"
                f"Используйте команду /subscribe для покупки подписки или звёзд.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "🗣️ Отправьте голосовое сообщение или наберите текст вопроса:",
        reply_markup=get_cancel_keyboard()
    )
    
    return VOICE_QUESTION

# Voice question handler - process voice
@ErrorHandler.handle_telegram_handler_errors
async def voice_question_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the voice question"""
    user = update.effective_user
    
    # Get user_id from context to avoid DetachedInstanceError
    user_id = context.user_data.get('user_id')
    
    # If user_id is not in context, get it from the database
    if not user_id:
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
    
    # Check if user has reached their limits
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'voice')
    
    if not has_free_limit:
        # Try to use stars
        success, message = await PaymentService.use_stars_for_service(user_id, 'voice')
        if not success:
            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    try:
        # Download the voice message
        voice_file = await update.message.voice.get_file()
        
        # Create a temporary file to save the voice message
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            voice_path = temp_file.name
        
        # Download the voice file to the temporary file
        await voice_file.download_to_drive(voice_path)
        
        # Transcribe the voice message
        logger.info(f"Transcribing voice message for user {user_id}")
        transcription = await openai_service.transcribe_audio(voice_path)
        
        if not transcription:
            await update.message.reply_text(
                "❌ Не удалось распознать голосовое сообщение. Пожалуйста, попробуйте еще раз или введите текстовый вопрос.",
                reply_markup=get_main_keyboard()
            )
            # Clean up the temporary file
            os.unlink(voice_path)
            return ConversationHandler.END
        
        # Send the transcription to the user
        await update.message.reply_text(
            f"🔊 Ваше сообщение: {transcription}",
            reply_markup=None
        )
        
        # Generate response using OpenAI
        logger.info(f"Generating response for voice transcription: {transcription}")
        response, tokens = await openai_service.generate_text_response(transcription)
        
        # Get advertisement
        ad_text = await AdminService.get_advertisement()
        ad_footer = f"\n\n---\n{ad_text}" if ad_text else ""
        
        # Send response
        await update.message.reply_text(
            f"{response}{ad_footer}",
            reply_markup=get_main_keyboard()
        )
        
        # Update user usage
        await UserService.update_user_usage(user_id, 'voice')
        
        # Log message
        await UserService.log_message(user_id, 'voice', transcription, response, tokens)
        
        # Clean up the temporary file
        os.unlink(voice_path)
        
    except Exception as e:
        logger.error(f"Error processing voice question: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке вашего голосового сообщения. Пожалуйста, попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
        # Clean up the temporary file if it exists
        if 'voice_path' in locals():
            os.unlink(voice_path)
    
    return ConversationHandler.END
