from aiogram import Dispatcher

from app.bot.handlers.answer_handlers import AnswerHandlers
from app.bot.handlers.display_info import DisplayInfo
from app.bot.handlers.purchase_handlers import PurchaseHandlers
from app.bot.handlers.question import question_handler
from app.bot.handlers.start import StartHandler
from app.bot.handlers.subscription_handlers import SubscriptionHandlers
from app.bot.handlers.admin_handlers import AdminHandlers
from app.bot.handlers.midjourney_handlers import MidJourneyHandlers
from app.bot.handlers.referral_handlers import ReferralHandlers
from app.bot.handlers.telegram_stars_handlers import TelegramStarsHandlers

from aiogram.filters.command import Command
from app.bot.utils import States
from aiogram import F

from app.services.openaitools import OpenAiTools
from app.services.db import DataBase
from app.services.stablediffusion import StableDiffusion
from app.services.cryptopay import CryptoPay
from app.services.midjourney import MidJourney
from app.services.telegram_stars import TelegramStarsService

def register_handlers(dp: Dispatcher, database: DataBase, openai: OpenAiTools, stable: StableDiffusion, 
                     crypto: CryptoPay, midjourney: MidJourney, telegram_stars: TelegramStarsService):
    # Заменяем регистрацию обработчиков крипто-оплаты на регистрацию обработчиков Telegram Stars
    # register_purchase_handlers(dp, database, crypto)
    register_telegram_stars_handlers(dp, database, telegram_stars)

    register_start_handlers(dp, database)

    register_question_handlers(dp)

    register_display_info_handlers(dp, database, telegram_stars)

    register_answer_handlers(dp, database, openai, stable)
    
    register_midjourney_handlers(dp, database, midjourney)
    
    register_subscription_handlers(dp, database, telegram_stars)
    
    register_admin_handlers(dp, database)
    
    register_referral_handlers(dp, database)
    
    register_telegram_stars_handlers(dp, database, telegram_stars)

def register_purchase_handlers(dp: Dispatcher, database: DataBase, crypto: CryptoPay):
    Purchase_Handlers = PurchaseHandlers(database, crypto)

    dp.message.register(Purchase_Handlers.purchase_handler, States.INFO_STATE, F.text.regexp(r'^Buy tokens and generations$'))
    dp.message.register(Purchase_Handlers.purchase_handler, States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Purchase_Handlers.purchase_handler,States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Purchase_Handlers.purchase_handler, States.PURCHASE_STABLE_STATE, F.text.regexp(r'^Back$'))

    currencies = ['USDT', 'TON', 'BTC', 'ETH']
    for currency in currencies:
        dp.message.register(Purchase_Handlers.buy_handler, States.PURCHASE_CHATGPT_STATE, F.text.regexp(rf'^{currency}$'))
        dp.message.register(Purchase_Handlers.buy_handler, States.PURCHASE_DALL_E_STATE, F.text.regexp(rf'^{currency}$'))
        dp.message.register(Purchase_Handlers.buy_handler, States.PURCHASE_STABLE_STATE, F.text.regexp(rf'^{currency}$'))

    dp.message.register(Purchase_Handlers.currencies_handler, States.PURCHASE_STATE, F.text.regexp(r'^100K ChatGPT tokens - 5 USD$'))
    dp.message.register(Purchase_Handlers.currencies_handler, States.PURCHASE_STATE, F.text.regexp(r'^50 DALL·E image generations - 5 USD$'))
    dp.message.register(Purchase_Handlers.currencies_handler, States.PURCHASE_STATE, F.text.regexp(r'^50 Stable Diffusion image generations - 5 USD$'))

def register_start_handlers(dp: Dispatcher, database: DataBase):
    Start_Handler = StartHandler(database)
    dp.message.register(Start_Handler.start_handler, Command('start'))
    dp.message.register(Start_Handler.start_handler, States.ENTRY_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.CHATGPT_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.DALL_E_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.STABLE_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.INFO_STATE, F.text.regexp(r'^Back$'))
    
    dp.message.register(Start_Handler.start_handler, States.MIDJOURNEY_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.SUBSCRIPTION_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.ADMIN_STATE, F.text.regexp(r'^Back$'))
    dp.message.register(Start_Handler.start_handler, States.REFERRAL_STATE, F.text.regexp(r'^Back$'))

def register_question_handlers(dp: Dispatcher):
    # Исправлены названия кнопок в соответствии с тем, как они отображаются в интерфейсе
    dp.message.register(question_handler, States.ENTRY_STATE, F.text.regexp(r'^💭Chatting — ChatGPT-4o$'))
    dp.message.register(question_handler, States.ENTRY_STATE, F.text.regexp(r'^🌄Image generation — DALL·E 3$'))
    dp.message.register(question_handler, States.ENTRY_STATE, F.text.regexp(r'^🌅Image generation — Stable Diffusion 3$'))
    dp.message.register(question_handler, States.ENTRY_STATE, F.text.regexp(r'^🖼️Images — MidJourney$'))

def register_display_info_handlers(dp: Dispatcher, database: DataBase, telegram_stars: TelegramStarsService):
    Display_Info = DisplayInfo(database)
    telegram_stars_handlers = TelegramStarsHandlers(database, telegram_stars)
    
    dp.message.register(Display_Info.display_info_handler, States.ENTRY_STATE, F.text.regexp(r'^👤My account | 💰Buy$'))
    dp.message.register(Display_Info.display_info_handler, States.ENTRY_STATE, F.text.regexp(r'^📊Subscriptions$'))
    dp.message.register(Display_Info.display_info_handler, States.ENTRY_STATE, F.text.regexp(r'^📈Referral program$'))
    
    # Ссылка на Start_Handler для кнопки назад
    start_handler = StartHandler(database)
    dp.message.register(start_handler.start_handler, States.INFO_STATE, F.text.regexp(r'^🔙Back$'))
    dp.message.register(start_handler.start_handler, States.PURCHASE_STATE, F.text.regexp(r'^🔙Back$'))
    
    dp.message.register(telegram_stars_handlers.stars_menu_handler, States.INFO_STATE, F.text.regexp(r'^💫Buy tokens and generations$'))

def register_answer_handlers(dp: Dispatcher, database: DataBase, openai: OpenAiTools, stable: StableDiffusion):
    Answer_Handlers = AnswerHandlers(database, openai, stable)
    dp.message.register(Answer_Handlers.chatgpt_answer_handler, States.CHATGPT_STATE, F.text)
    dp.message.register(Answer_Handlers.stable_answer_handler, States.STABLE_STATE, F.text)
    dp.message.register(Answer_Handlers.dall_e_answer_handler, States.DALL_E_STATE, F.text)

def register_midjourney_handlers(dp: Dispatcher, database: DataBase, midjourney: MidJourney):
    midjourney_handlers = MidJourneyHandlers(database, midjourney)
    dp.message.register(midjourney_handlers.midjourney_start_handler, States.ENTRY_STATE, F.text.regexp(r'^🖼️Images — MidJourney$'))
    dp.message.register(midjourney_handlers.process_midjourney_request, States.MIDJOURNEY_STATE, F.text)

def register_subscription_handlers(dp: Dispatcher, database: DataBase, telegram_stars: TelegramStarsService):
    subscription_handlers = SubscriptionHandlers(database, telegram_stars)
    dp.message.register(subscription_handlers.show_subscriptions_handler, Command('subscriptions'))
    dp.message.register(subscription_handlers.show_subscriptions_handler, States.ENTRY_STATE, F.text.regexp(r'^Subscriptions$'))
    
    dp.callback_query.register(subscription_handlers.show_chat_plans_handler, F.data == "show_chat_plans")
    dp.callback_query.register(subscription_handlers.show_image_plans_handler, F.data == "show_image_plans")
    dp.callback_query.register(subscription_handlers.stars_balance_handler, F.data == "stars_balance")
    
    dp.callback_query.register(subscription_handlers.buy_subscription_handler, F.data.startswith("buy_chat_"))
    
    dp.callback_query.register(subscription_handlers.buy_subscription_handler, F.data.startswith("buy_image_"))
    
    dp.callback_query.register(subscription_handlers.confirm_subscription_handler, F.data.startswith("confirm_sub_"))
    
    dp.callback_query.register(subscription_handlers.check_subscription_status_handler, F.data == "check_sub_status")

def register_admin_handlers(dp: Dispatcher, database: DataBase):
    admin_handlers = AdminHandlers(database)
    dp.message.register(admin_handlers.admin_panel_handler, Command('admin'))
    
    dp.callback_query.register(admin_handlers.admin_stats_handler, F.data == "admin_stats")
    # убирать отсюда обработчик
    # dp.callback_query.register(admin_handlers.admin_users_handler, F.data == "admin_users")
    # dp.callback_query.register(admin_handlers.admin_sales_handler, F.data == "admin_sales")
    # dp.callback_query.register(admin_handlers.admin_banned_handler, F.data == "admin_banned")
    dp.callback_query.register(admin_handlers.admin_add_balance_start, F.data == "admin_add_balance")
    # dp.callback_query.register(admin_handlers.admin_add_admin_start, F.data == "admin_add_admin")
    
    dp.message.register(admin_handlers.admin_add_balance_process, States.ADMIN_ADD_BALANCE_STATE)
    # dp.message.register(admin_handlers.admin_add_admin_process, States.ADMIN_ADD_ADMIN_STATE)
    
    dp.callback_query.register(admin_handlers.admin_back_to_main_handler, F.data == "back_to_admin")

def register_referral_handlers(dp: Dispatcher, database: DataBase):
    referral_handlers = ReferralHandlers(database)
    dp.message.register(referral_handlers.show_referral_program_handler, Command('referral'))
    dp.message.register(referral_handlers.show_referral_program_handler, States.ENTRY_STATE, F.text.regexp(r'^Referral program$'))
    
    dp.callback_query.register(referral_handlers.show_referrals_list_handler, F.data == "show_referrals_list")
    dp.callback_query.register(referral_handlers.back_to_referral_program_handler, F.data == "back_to_referral_program")
    
def register_telegram_stars_handlers(dp: Dispatcher, database: DataBase, telegram_stars: TelegramStarsService):
    telegram_stars_handlers = TelegramStarsHandlers(database, telegram_stars)
    start_handler = StartHandler(database)  
    
    dp.message.register(telegram_stars_handlers.stars_balance_handler, Command('stars'))
    dp.message.register(telegram_stars_handlers.buy_stars_handler, Command('buy'))
    
    dp.message.register(telegram_stars_handlers.check_stars_balance, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^Check balance$'))
    dp.message.register(telegram_stars_handlers.send_invoice_handler, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^100K ChatGPT tokens - 20 stars$'))
    dp.message.register(telegram_stars_handlers.send_invoice_handler, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^50 DALL·E image generations - 20 stars$'))
    dp.message.register(telegram_stars_handlers.send_invoice_handler, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^50 Stable Diffusion image generations - 20 stars$'))
    dp.message.register(telegram_stars_handlers.send_invoice_handler, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^50 MidJourney image generations - 20 stars$'))
    dp.message.register(start_handler.start_handler, States.TELEGRAM_STARS_MENU_STATE, F.text.regexp(r'^Back$'))
    
    dp.pre_checkout_query.register(telegram_stars_handlers.pre_checkout_handler)
    dp.message.register(telegram_stars_handlers.success_payment_handler, F.successful_payment)