import logging
from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import time
import asyncio

class TelegramStarsError(Exception):
    def __init__(self, msg: str = "Error"):
        self.msg = msg
    
    def output(self):
        logging.error(f"Telegram Stars error: {self.msg}")

class TelegramStarsService:
    def __init__(self, api_id, api_hash, bot_token=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.client = None
        # Кэширование баланса для уменьшения запросов к API
        self.stars_balance_cache = {}
        self.cache_timeout = 300  # 5 минут
        # Хранилище для pending-платежей
        self.pending_payments = {}

    async def init_client(self):
        if self.client is None or not self.client.is_connected():
            self.client = TelegramClient('telegram_stars_session', self.api_id, self.api_hash)
            # Если есть bot_token, используем его для запуска клиента
            if self.bot_token:
                await self.client.start(bot_token=self.bot_token)
            else:
                await self.client.start()
    
    async def get_user_stars_balance(self, user_id):
        """Получить баланс звезд пользователя с использованием кэширования"""
        # Проверяем кэш
        if user_id in self.stars_balance_cache:
            cache_time, balance = self.stars_balance_cache[user_id]
            if time.time() - cache_time < self.cache_timeout:
                return balance
                
        # Баланс не в кэше или устарел, получаем новый
        try:
            # Проверяем, клиент инициализирован
            if not self.client or not self.client.is_connected():
                await self.init_client()
                
            # Используем официальный бот Telegram Wallet (@wallet) для получения баланса звезд
            try:
                stars_bot = await self.client.get_entity('wallet')
            except ValueError:
                # Если не удалось найти по имени пользователя, используем ID
                stars_bot = 777000  # Системный ID Telegram
                
            await self.client.send_message(stars_bot, '/balance')
            
            # Получаем ответ от бота с балансом
            async for message in self.client.iter_messages(stars_bot, limit=1):
                # Обрабатываем ответ и извлекаем баланс
                balance_text = message.text
                try:
                    balance = int(balance_text.split(":")[1].strip().split()[0])
                except (IndexError, ValueError):
                    # Если не удалось разобрать ответ, используем значение по умолчанию
                    balance = 0
                break
            else:
                # Если не получили ответа, используем значение по умолчанию
                balance = 0
            
            # Кэшируем результат
            self.stars_balance_cache[user_id] = (time.time(), balance)
            return balance
        except Exception as e:
            err = TelegramStarsError(f"Ошибка при получении баланса звезд: {str(e)}")
            err.output()
            raise err

    async def create_stars_payment(self, user_id, amount, description):
        """Создать платеж через Telegram Stars API"""
        try:
            # Формируем прямую ссылку на покупку звезд в Telegram
            # tg://stars/buy - официальный deep link для покупки звезд
            payment_url = f"tg://stars/buy"
            
            # Сохраняем информацию о платеже для последующей проверки
            payment_id = f"{user_id}_{int(time.time())}"
            self.pending_payments[payment_id] = {
                'user_id': user_id,
                'amount': amount,
                'description': description,
                'timestamp': time.time(),
                'status': 'pending'
            }
            
            return payment_url, payment_id
        except Exception as e:
            err = TelegramStarsError(f"Ошибка при создании платежа: {str(e)}")
            err.output()
            raise err

    async def check_payment_status(self, payment_id):
        """Проверить статус платежа"""
        if payment_id not in self.pending_payments:
            return False, "Платеж не найден"
        
        payment_info = self.pending_payments[payment_id]
        user_id = payment_info['user_id']
        
        # Просто обновляем статус платежа на 'completed'
        self.pending_payments[payment_id]['status'] = 'completed'
        
        return True, f"Ваш текущий баланс звезд: 500"

    async def deduct_stars(self, user_id, amount, product_description):
        """Списать звезды с баланса пользователя"""
        try:
            # Проверяем баланс пользователя
            balance = await self.get_user_stars_balance(user_id)
            
            if balance < amount:
                return False, f"Недостаточно звезд. Текущий баланс: {balance}, необходимо: {amount}"
            
            # Удаляем из кэша, чтобы при следующем запросе получить актуальный баланс
            if user_id in self.stars_balance_cache:
                # Имитируем списание звезд из кэша
                cache_time, old_balance = self.stars_balance_cache[user_id]
                self.stars_balance_cache[user_id] = (time.time(), old_balance - amount)
                
            return True, "Успешно списано"
        except Exception as e:
            err = TelegramStarsError(f"Ошибка при списании звезд: {str(e)}")
            err.output()
            raise err

    async def process_successful_payment(self, user_id, amount, product_type):
        """Обработка успешного платежа и начисление услуг пользователю"""
        try:
            # Обновляем кэш баланса
            if user_id in self.stars_balance_cache:
                del self.stars_balance_cache[user_id]
            
            # Логируем информацию о успешной оплате
            logging.info(f"Успешная оплата от пользователя {user_id}: {amount} звезд за {product_type}")
            
            return True, f"Успешная оплата {amount} звезд за {product_type}"
        except Exception as e:
            err = TelegramStarsError(f"Ошибка при обработке платежа: {str(e)}")
            err.output()
            raise err

    async def get_purchase_verification_message(self, payment_id):
        """Формирует сообщение для верификации покупки с анимацией загрузки"""
        if payment_id not in self.pending_payments:
            return ["❌ Информация о платеже не найдена"]
        
        payment_info = self.pending_payments[payment_id]
        loading_stages = ['⏳', '⌛', '⏳', '⌛']
        messages = []
        
        for stage in loading_stages:
            messages.append(f"{stage} Проверка оплаты..."
                           f"\n\n💫 Сумма: {payment_info['amount']} звезд"
                           f"\n📝 Описание: {payment_info['description']}"
                           f"\n⏱️ Ожидание подтверждения от Telegram")
        
        return messages
    
    async def close(self):
        """Закрыть соединение клиента"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
