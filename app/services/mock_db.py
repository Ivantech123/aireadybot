from app.services.db import DataBase, DatabaseError

class MockDatabase(DataBase):
    """Мок-класс для базы данных, используемый для тестирования без PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        # Симулируем кэш пользователей
        self._users = {}
        self._admins = {1234567890: True}  # Демо админ ID
        self._subscriptions = {}
        
    async def is_user(self, user_id):
        """Проверяет, существует ли пользователь"""
        return user_id in self._users or True  # Всегда возвращаем True для тестирования
    
    async def is_admin(self, user_id):
        """Проверяет, является ли пользователь администратором"""
        return self._admins.get(user_id, False)
    
    async def get_user_balance(self, user_id, balance_type):
        """Возвращает баланс пользователя"""
        # Возвращаем тестовые данные
        if balance_type == 'chatgpt':
            return 100
        elif balance_type == 'dall_e':
            return 50
        elif balance_type == 'stable':
            return 50
        elif balance_type == 'midjourney':
            return 25
        return 0
    
    async def update_user_balance(self, user_id, balance_type, amount):
        """Обновляет баланс пользователя"""
        # Для тестирования просто печатаем информацию
        print(f"Обновлен баланс пользователя {user_id}, {balance_type}: {amount}")
        return True
    
    async def create_user(self, user_id, username, first_name, last_name, language_code='en'):
        """Создает нового пользователя"""
        self._users[user_id] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'language_code': language_code
        }
        print(f"Создан пользователь {user_id} ({username})")
        return True
    
    async def has_subscription(self, user_id, subscription_type):
        """Проверяет, есть ли у пользователя подписка"""
        return self._subscriptions.get(user_id, {}).get(subscription_type, False)
    
    async def add_subscription(self, user_id, subscription_type, days):
        """Добавляет подписку пользователю"""
        if user_id not in self._subscriptions:
            self._subscriptions[user_id] = {}
        self._subscriptions[user_id][subscription_type] = True
        print(f"Добавлена подписка {subscription_type} пользователю {user_id} на {days} дней")
        return True
