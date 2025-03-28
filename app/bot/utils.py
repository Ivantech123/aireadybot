from aiogram.fsm.state import State, StatesGroup
from tiktoken import encoding_for_model
from gpytranslate import Translator
import logging

class States(StatesGroup):
    ENTRY_STATE = State()
    CHATGPT_STATE = State()
    DALL_E_STATE = State()
    STABLE_STATE = State()
    INFO_STATE = State()
    PURCHASE_STATE = State()
    PURCHASE_CHATGPT_STATE = State()
    PURCHASE_DALL_E_STATE = State()
    PURCHASE_STABLE_STATE = State()
    # Новые состояния для MidJourney
    MIDJOURNEY_STATE = State()
    PURCHASE_MIDJOURNEY_STATE = State()
    # Состояния для подписок
    SUBSCRIPTION_STATE = State()
    # Состояния для админ-панели
    ADMIN_STATE = State()
    ADMIN_ADD_BALANCE_STATE = State()
    ADMIN_ADD_ADMIN_STATE = State()
    # Состояния для реферальной системы
    REFERRAL_STATE = State()
    # Состояния для Telegram Stars
    TELEGRAM_STARS_MENU_STATE = State()

encoding = encoding_for_model("gpt-4o")

translator = Translator()

class TelegramError(Exception):
    def __init__(self, msg: str = "Error"):
        self.msg=msg
    def output(self):
        logging.error("Telegram error:", self.msg)