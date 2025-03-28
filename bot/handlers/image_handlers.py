import os
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
IMAGE_GENERATION = range(1)

# OpenAI service instance
openai_service = OpenAIService()

# Get image generation cost from config
IMAGE_GENERATION_STARS_COST = int(config.get('IMAGE_GENERATION_STARS_COST', 5))

# Image generation handler - entry point
@ErrorHandler.handle_telegram_handler_errors
async def image_generation_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the image generation conversation"""
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
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'image')
    
    if not has_free_limit:
        # Check if user has enough stars
        has_stars, stars_count, cost = await PaymentService.check_stars_for_service(user_id, 'image')
        
        if not has_stars:
            await update.message.reply_text(
                f"❌ Вы достигли лимита бесплатных генераций изображений на сегодня.\n\n"
                f"Для продолжения вам необходимо приобрести звёзды или подписку.\n\n"
                f"У вас {stars_count} звёзд, а требуется {IMAGE_GENERATION_STARS_COST} звёзд за одну генерацию.\n\n"
                f"Используйте команду /subscribe для покупки звёзд или подписки.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "Опишите изображение, которое хотите сгенерировать:",
        reply_markup=get_cancel_keyboard()
    )
    
    return IMAGE_GENERATION

# Image generation handler - process prompt
@ErrorHandler.handle_telegram_handler_errors
async def image_generation_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the image generation prompt"""
    user = update.effective_user
    prompt = update.message.text
    
    # Send uploading photo action
    await update.message.chat.send_action(action="upload_photo")
    
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
    has_free_limit, remaining = await UserService.check_user_limits(user_id, 'image')
    
    if not has_free_limit:
        # Try to use stars
        success, message = await PaymentService.use_stars_for_service(user_id, 'image')
        if not success:
            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    try:
        # Generate image using OpenAI
        logger.info(f"Generating image for prompt: {prompt}")
        image_url = await openai_service.generate_image(prompt)
        
        if not image_url:
            await update.message.reply_text(
                "❌ Не удалось сгенерировать изображение. Пожалуйста, попробуйте другой запрос.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        # Get advertisement
        ad_text = await AdminService.get_advertisement()
        
        # Send image
        await update.message.reply_photo(
            photo=image_url,
            caption=f"Сгенерировано по запросу: {prompt}" + (f"\n\n---\n{ad_text}" if ad_text else ""),
            reply_markup=get_main_keyboard()
        )
        
        # Update user usage
        await UserService.update_user_usage(user_id, 'image')
        
        # Log message
        await UserService.log_message(user_id, 'image', prompt, image_url, 0)
        
    except Exception as e:
        logger.error(f"Error processing image generation: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при генерации изображения. Пожалуйста, попробуйте еще раз позже.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END
