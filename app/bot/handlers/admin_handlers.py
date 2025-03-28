from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from app.bot.utils import States, TelegramError
from app.services.db import DataBase, DatabaseError

class AdminHandlers:
    def __init__(self, database: DataBase):
        self.database = database
    
    async def admin_panel_handler(self, message: Message, state: FSMContext):
        """u041fu043eu043au0430u0437u044bu0432u0430u0435u0442 u0430u0434u043cu0438u043d-u043fu0430u043du0435u043bu044c"""
        try:
            user_id = message.from_user.id
            
            # u041fu0440u043eu0432u0435u0440u044fu0435u043c, u044fu0432u043bu044fu0435u0442u0441u044f u043bu0438 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044c u0430u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u043eu0440u043eu043c
            admin_role = await self.database.is_admin(user_id)
            
            if not admin_role:
                await message.answer("u2757ufe0f u0423 u0432u0430u0441 u043du0435u0442 u0434u043eu0441u0442u0443u043fu0430 u043a u0430u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u0438u0432u043du043eu0439 u043fu0430u043du0435u043bu0438.")
                return
            
            # u0421u043eu0437u0434u0430u0435u043c u043au043du043eu043fu043au0438 u0434u043bu044f u0430u0434u043cu0438u043d-u043fu0430u043du0435u043bu0438
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ud83dudcca u0421u0442u0430u0442u0438u0441u0442u0438u043au0430", callback_data="admin_stats")],
                [InlineKeyboardButton(text="ud83dudc65 u0423u043fu0440u0430u0432u043bu0435u043du0438u0435 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044fu043cu0438", callback_data="admin_users")],
                [InlineKeyboardButton(text="ud83dudcc8 u041fu0440u043eu0434u0430u0436u0438", callback_data="admin_sales")],
                [InlineKeyboardButton(text="ud83duded1 u0417u0430u0431u043bu043eu043au0438u0440u043eu0432u0430u043du043du044bu0435 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0438", callback_data="admin_banned")],
                [InlineKeyboardButton(text="ud83dudcb3 u0414u043eu0431u0430u0432u0438u0442u044c u0431u0430u043bu0430u043du0441 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044e", callback_data="admin_add_balance")]
            ])
            
            await message.answer(
                f"ud83dudee0 u0410u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u0438u0432u043du0430u044f u043fu0430u043du0435u043bu044c\n\n"
                f"u0412u0430u0448u0430 u0440u043eu043bu044c: {admin_role}\n\n"
                f"u0412u044bu0431u0435u0440u0438u0442u0435 u0434u0435u0439u0441u0442u0432u0438u0435:",
                reply_markup=keyboard
            )
            
            await state.set_state(States.ADMIN_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def admin_stats_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """u041fu043eu043au0430u0437u044bu0432u0430u0435u0442 u0441u0442u0430u0442u0438u0441u0442u0438u043au0443 u0431u043eu0442u0430"""
        try:
            await callback_query.answer()
            
            async with self.database.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    # u041eu0431u0449u0435u0435 u043au043eu043bu0438u0447u0435u0441u0442u0432u043e u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0435u0439
                    await cursor.execute("SELECT COUNT(*) FROM users")
                    total_users = (await cursor.fetchone())[0]
                    
                    # u041au043eu043bu0438u0447u0435u0441u0442u0432u043e u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0435u0439 u0441 u0430u043au0442u0438u0432u043du044bu043cu0438 u043fu043eu0434u043fu0438u0441u043au0430u043cu0438
                    await cursor.execute("SELECT COUNT(DISTINCT user_id) FROM subscriptions WHERE end_date > NOW()")
                    users_with_subs = (await cursor.fetchone())[0]
                    
                    # u041au043eu043bu0438u0447u0435u0441u0442u0432u043e u0430u043au0442u0438u0432u043du044bu0445 u043fu043eu0434u043fu0438u0441u043eu043a u043fu043e u0442u0438u043fu0430u043c
                    await cursor.execute("SELECT type, COUNT(*) FROM subscriptions WHERE end_date > NOW() GROUP BY type")
                    sub_types = await cursor.fetchall()
                    
                    # u0421u0442u0430u0442u0438u0441u0442u0438u043au0430 u043fu043e u0440u0435u0444u0435u0440u0430u043bu0430u043c
                    await cursor.execute("SELECT COUNT(*) FROM referrals")
                    total_referrals = (await cursor.fetchone())[0]
                    
                    # u0421u0442u0430u0442u0438u0441u0442u0438u043au0430 u043fu043e u0441u043eu043eu0431u0449u0435u043du0438u044fu043c
                    await cursor.execute("SELECT COUNT(*) FROM messages")
                    total_messages = (await cursor.fetchone())[0]
            
            # u0424u043eu0440u043cu0438u0440u0443u0435u043c u0441u0442u0430u0442u0438u0441u0442u0438u043au0443
            stats_text = f"ud83dudcca u0421u0442u0430u0442u0438u0441u0442u0438u043au0430 u0431u043eu0442u0430:\n\n"
            stats_text += f"\ud83d\udc65 u0412u0441u0435u0433u043e u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0435u0439: {total_users}\n"
            stats_text += f"\ud83d\udc64 u041fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0435u0439 u0441 u043fu043eu0434u043fu0438u0441u043au0430u043cu0438: {users_with_subs}\n\n"
            
            stats_text += "ud83dudcc6 u0410u043au0442u0438u0432u043du044bu0435 u043fu043eu0434u043fu0438u0441u043au0438:\n"
            for sub_type in sub_types:
                type_name = "\ud83d\udcac u0427u0430u0442" if sub_type[0] == "chat" else "\ud83d\uddbc u041au0430u0440u0442u0438u043du043au0438"
                stats_text += f"{type_name}: {sub_type[1]}\n"
            
            stats_text += f"\n\ud83d\udcac u0412u0441u0435u0433u043e u0441u043eu043eu0431u0449u0435u043du0438u0439: {total_messages}\n"
            stats_text += f"\ud83d\udc6b u0412u0441u0435u0433u043e u0440u0435u0444u0435u0440u0430u043bu043eu0432: {total_referrals}\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ud83dudd19 u041du0430u0437u0430u0434", callback_data="admin_back_to_main")]
            ])
            
            await callback_query.message.edit_text(stats_text, reply_markup=keyboard)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def admin_add_balance_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """u041du0430u0447u0438u043du0430u0435u0442 u043fu0440u043eu0446u0435u0441u0441 u0434u043eu0431u0430u0432u043bu0435u043du0438u044f u0431u0430u043bu0430u043du0441u0430 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044e"""
        try:
            await callback_query.answer()
            
            await callback_query.message.edit_text(
                "ud83dudcb3 u0412u0432u0435u0434u0438u0442u0435 Telegram ID u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f u0438 u0442u0438u043f u0431u0430u043bu0430u043du0441u0430 u0432 u0444u043eu0440u043cu0430u0442u0435:\n"
                "ID u0442u0438u043f u043au043eu043bu0438u0447u0435u0441u0442u0432u043e\n\n"
                "u041fu0440u0438u043cu0435u0440: 123456789 chatgpt 5000\n"
                "u0422u0438u043fu044b u0431u0430u043bu0430u043du0441u0430: chatgpt, dall_e, stable, midjourney"
            )
            
            await state.set_state(States.ADMIN_ADD_BALANCE_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def admin_add_balance_process(self, message: Message, state: FSMContext):
        """u041eu0431u0440u0430u0431u0430u0442u044bu0432u0430u0435u0442 u0434u043eu0431u0430u0432u043bu0435u043du0438u0435 u0431u0430u043bu0430u043du0441u0430 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044e"""
        try:
            parts = message.text.split()
            
            if len(parts) != 3:
                await message.answer("u041du0435u0432u0435u0440u043du044bu0439 u0444u043eu0440u043cu0430u0442. u041fu043eu0436u0430u043bu0443u0439u0441u0442u0430, u0443u043au0430u0436u0438u0442u0435 u0432 u0444u043eu0440u043cu0430u0442u0435: ID u0442u0438u043f u043au043eu043bu0438u0447u0435u0441u0442u0432u043e")
                return
            
            try:
                user_id = int(parts[0])
                balance_type = parts[1].lower()
                amount = int(parts[2])
            except ValueError:
                await message.answer("u041du0435u0432u0435u0440u043du044bu0439 u0444u043eu0440u043cu0430u0442. ID u0438 u043au043eu043bu0438u0447u0435u0441u0442u0432u043e u0434u043eu043bu0436u043du044b u0431u044bu0442u044c u0447u0438u0441u043bu0430u043cu0438.")
                return
            
            if balance_type not in ['chatgpt', 'dall_e', 'stable', 'midjourney']:
                await message.answer("u041du0435u0432u0435u0440u043du044bu0439 u0442u0438u043f u0431u0430u043bu0430u043du0441u0430. u0414u043eu0441u0442u0443u043fu043du044bu0435 u0442u0438u043fu044b: chatgpt, dall_e, stable, midjourney")
                return
            
            # u041fu0440u043eu0432u0435u0440u044fu0435u043c, u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u043bu0438 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044c
            user_exists = await self.database.is_user(user_id)
            
            if not user_exists:
                await message.answer(f"u041fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044c u0441 ID {user_id} u043du0435 u043du0430u0439u0434u0435u043d.")
                return
            
            # u041eu0431u043du043eu0432u043bu044fu0435u043c u0431u0430u043bu0430u043du0441
            async with self.database.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f"UPDATE users SET {balance_type} = {balance_type} + %s WHERE user_id = %s", (amount, user_id))
                    await conn.commit()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ud83dudd19 u041du0430u0437u0430u0434 u0432 u0430u0434u043cu0438u043d-u043fu0430u043du0435u043bu044c", callback_data="admin_back_to_main")]
            ])
            
            await message.answer(
                f"u2705 u0411u0430u043bu0430u043du0441 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f u0441 ID {user_id} u0443u0441u043fu0435u0448u043du043e u043fu043eu043fu043eu043bu043du0435u043d.\n"
                f"u0422u0438u043f u0431u0430u043bu0430u043du0441u0430: {balance_type}\n"
                f"u0414u043eu0431u0430u0432u043bu0435u043du043e: +{amount}",
                reply_markup=keyboard
            )
            
            await state.set_state(States.ADMIN_STATE)
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
    
    async def admin_back_to_main_handler(self, callback_query: types.CallbackQuery, state: FSMContext):
        """u0412u043eu0437u0432u0440u0430u0449u0430u0435u0442 u043a u0433u043bu0430u0432u043du043eu043cu0443 u043cu0435u043du044e u0430u0434u043cu0438u043d-u043fu0430u043du0435u043bu0438"""
        try:
            await callback_query.answer()
            
            user_id = callback_query.from_user.id
            admin_role = await self.database.is_admin(user_id)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ud83dudcca u0421u0442u0430u0442u0438u0441u0442u0438u043au0430", callback_data="admin_stats")],
                [InlineKeyboardButton(text="ud83dudc65 u0423u043fu0440u0430u0432u043bu0435u043du0438u0435 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044fu043cu0438", callback_data="admin_users")],
                [InlineKeyboardButton(text="ud83dudcc8 u041fu0440u043eu0434u0430u0436u0438", callback_data="admin_sales")],
                [InlineKeyboardButton(text="ud83duded1 u0417u0430u0431u043bu043eu043au0438u0440u043eu0432u0430u043du043du044bu0435 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu0438", callback_data="admin_banned")],
                [InlineKeyboardButton(text="ud83dudcb3 u0414u043eu0431u0430u0432u0438u0442u044c u0431u0430u043bu0430u043du0441 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044e", callback_data="admin_add_balance")]
            ])
            
            await callback_query.message.edit_text(
                f"ud83dudee0 u0410u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u0438u0432u043du0430u044f u043fu0430u043du0435u043bu044c\n\n"
                f"u0412u0430u0448u0430 u0440u043eu043bu044c: {admin_role}\n\n"
                f"u0412u044bu0431u0435u0440u0438u0442u0435 u0434u0435u0439u0441u0442u0432u0438u0435:",
                reply_markup=keyboard
            )
        except Exception as e:
            err = TelegramError(str(e))
            err.output()
            raise err
