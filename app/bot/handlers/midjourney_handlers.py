from aiogram import types
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from app.bot.utils import States, TelegramError
from app.services.db import DataBase, DatabaseError
from app.services.midjourney import MidJourney, MidJourneyError
import os
import uuid
import asyncio

class MidJourneyHandlers:
    def __init__(self, database: DataBase, midjourney: MidJourney):
        self.database = database
        self.midjourney = midjourney
        # Создаем директорию для сохранения изображений, если она не существует
        self.images_dir = os.path.join(os.getcwd(), 'images', 'midjourney')
        os.makedirs(self.images_dir, exist_ok=True)

    async def midjourney_start_handler(self, message: Message, state: FSMContext):
        """Handler for starting image generation with MidJourney"""
        try:
            user_id = message.from_user.id
            
            # Check user subscription
            image_sub = await self.database.check_subscription(user_id, "image")
            if image_sub:
                # If user has subscription, check limits
                if image_sub['usage_today'] >= image_sub['daily_limit']:
                    await message.answer(
                        "❌ You have reached your daily limit for image generations.\n"
                        "Your limit will reset tomorrow or you can purchase a subscription with more generations."
                    )
                    return
            else:
                # If no subscription, check balance
                balance = await self.database.get_midjourney(user_id)
                if balance <= 0:
                    # Not enough generations
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="💰 Buy tokens", callback_data="show_image_plans")]
                    ])
                    
                    await message.answer(
                        "❌ You don't have enough MidJourney generations.\n"
                        "Purchase a subscription or add credits to continue.",
                        reply_markup=keyboard
                    )
                    return
            
            # Create keyboard with back button
            back_button = types.KeyboardButton(text="🔙Back")
            keyboard = types.ReplyKeyboardMarkup(keyboard=[[back_button]], resize_keyboard=True)
            
            # Send instructions and transition to waiting state
            await message.answer(
                "🖼 Image generation with MidJourney\n\n"
                "Describe the desired image in detail. For example:\n"
                "\"Photorealistic portrait of a woman in cyberpunk style with neon lights in the background\"\n\n"
                "Or use /cancel to cancel.",
                reply_markup=keyboard
            )
            
            await state.set_state(States.MIDJOURNEY_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def process_midjourney_request(self, message: Message, state: FSMContext):
        """Process MidJourney image generation request"""
        try:
            user_id = message.from_user.id
            prompt = message.text
            
            # If user sent /cancel or clicked Back, cancel generation
            if prompt.lower() == '/cancel' or prompt == '🔙Back':
                await message.answer("✅ Generation cancelled. Returning to main menu.")
                await state.set_state(States.ENTRY_STATE)
                return
            
            # Check request length
            if len(prompt) < 5:
                await message.answer(
                    "❌ Request is too short. Please describe the desired image in more detail."
                )
                return
            
            # Check user subscription and balance
            has_subscription = False
            image_sub = await self.database.check_subscription(user_id, "image")
            
            if image_sub:
                # If user has subscription, check limits
                if image_sub['usage_today'] >= image_sub['daily_limit']:
                    await message.answer(
                        "❌ You have reached your daily limit for image generations.\n"
                        "Your limit will reset tomorrow or you can purchase a subscription with more generations."
                    )
                    return
                has_subscription = True
            else:
                # If no subscription, check balance
                balance = await self.database.get_midjourney(user_id)
                if balance <= 0:
                    # Not enough generations
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="💰 Buy tokens", callback_data="show_image_plans")]
                    ])
                    
                    await message.answer(
                        "❌ You don't have enough MidJourney generations.\n"
                        "Purchase a subscription or add credits to continue.",
                        reply_markup=keyboard
                    )
                    return
            
            # Send message about starting generation
            loading_message = await message.answer("🔄 Generation started. This may take some time...")
            
            try:
                # Generate image with MidJourney with timeout
                try:
                    # Set timeout for request
                    import asyncio
                    # Create task for generating image
                    image_data_task = asyncio.create_task(self.midjourney.generate_image(prompt))
                    # Update message about starting generation
                    dots = ""
                    for i in range(4):  # Maximum number of updates (60 seconds)
                        if image_data_task.done():
                            break
                        if i > 0:  # Update message after first update
                            dots += "."
                            await loading_message.edit_text(f"🔄 Generation continues{dots} This may take up to 1-2 minutes.")
                        await asyncio.sleep(15)  # Wait 15 seconds
                    
                    # Wait for task completion with timeout
                    try:
                        image_data = await asyncio.wait_for(image_data_task, timeout=60)  # Timeout 60 seconds
                    except asyncio.TimeoutError:
                        # If request took too long, raise error
                        raise MidJourneyError("MidJourney API request took too long. Please try again later.")
                except asyncio.CancelledError:
                    raise MidJourneyError("Request was cancelled.")
                
                # If received base URL or base64, save image
                file_name = f"{user_id}_{uuid.uuid4()}.png"
                file_path = os.path.join(self.images_dir, file_name)
                
                # If URL, image is already saved on MidJourney server
                # If base64, need to decode and save
                if isinstance(image_data, str) and (image_data.startswith('http') or image_data.startswith('data:image')):
                    # If base64, decode
                    if image_data.startswith('data:image') or ';base64,' in image_data:
                        image_binary = await self.midjourney.decode_image(image_data)
                        with open(file_path, 'wb') as f:
                            f.write(image_binary)
                    else:
                        # If URL, download via aiohttp
                        import aiohttp
                        # Set timeout for HTTP request
                        timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds for entire request
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(image_data) as resp:
                                if resp.status == 200:
                                    image_binary = await resp.read()
                                    with open(file_path, 'wb') as f:
                                        f.write(image_binary)
                                else:
                                    raise MidJourneyError(f"Failed to download image: {resp.status}")
                # If binary data, just save
                elif isinstance(image_data, bytes):
                    with open(file_path, 'wb') as f:
                        f.write(image_data)
                else:
                    raise MidJourneyError(f"Unknown image data format: {type(image_data)}")
                
                # Now send image to user
                await message.bot.delete_message(chat_id=message.chat.id, message_id=loading_message.message_id)
                
                # Create object for sending file
                photo = FSInputFile(file_path)
                
                await message.answer_photo(
                    photo=photo,
                    caption=f"✅ Image generated by request:\n\"{prompt}\""
                )
                
                # Decrease user balance or update subscription usage
                if has_subscription:
                    await self.database.increment_subscription_usage(user_id, "image")
                else:
                    current_balance = await self.database.get_midjourney(user_id)
                    await self.database.set_midjourney(user_id, current_balance - 1)
                    
                    await message.answer(f"Remaining generations: {current_balance - 1}")
                
                # Delete file after sending, to avoid cluttering disk
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                
            except MidJourneyError as e:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=loading_message.message_id)
                await message.answer(f"❌ Error generating image: {str(e)}")
            
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
