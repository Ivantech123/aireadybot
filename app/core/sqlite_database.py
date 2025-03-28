import aiosqlite
import os
from typing import Optional, Dict, Any, List, Tuple

class SQLiteDataBaseCore:
    """Класс для работы с SQLite вместо PostgreSQL"""
    
    def __init__(self, db_url: str):
        # Извлекаем путь к файлу из URL
        if db_url.startswith('sqlite:///'):
            self.db_path = db_url[10:]
        else:
            self.db_path = db_url
        self.pool = self  # Совместимость с интерфейсом PostgreSQL
        self.conn = None
        
    async def open_pool(self) -> None:
        """Открываем соединение с базой данных"""
        self.conn = await aiosqlite.connect(self.db_path)
        # Настройка для получения словарей вместо кортежей
        self.conn.row_factory = aiosqlite.Row
        
    async def connection(self):
        """Возвращает объект для использования с контекстным менеджером"""
        if not self.conn:
            await self.open_pool()
        return SQLiteConnectionWrapper(self.conn)
    
    async def close(self) -> None:
        """Закрываем соединение с базой данных"""
        if self.conn:
            await self.conn.close()
            self.conn = None

class SQLiteConnectionWrapper:
    """Обертка для совместимости с контекстным менеджером PostgreSQL"""
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            await self.cursor.close()
            self.cursor = None
        
    async def cursor(self):
        """Создает курсор SQLite с интерфейсом, совместимым с PostgreSQL"""
        self.cursor = await self.conn.cursor()
        return SQLiteCursorWrapper(self.cursor, self.conn)
    
    async def commit(self):
        """Фиксирует изменения в базе данных"""
        await self.conn.commit()
        
class SQLiteCursorWrapper:
    """Обертка для совместимости курсора SQLite с PostgreSQL"""
    
    def __init__(self, cursor, conn):
        self.cursor = cursor
        self.conn = conn
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cursor.close()
        
    async def execute(self, query: str, params=None):
        """Выполняет SQL-запрос с параметрами"""
        # Преобразуем PostgreSQL плейсхолдеры (%s) в SQLite (?) 
        query = query.replace('%s', '?')
        await self.cursor.execute(query, params)
        return self
        
    async def fetchone(self):
        """Возвращает одну строку результата"""
        row = await self.cursor.fetchone()
        if row:
            return tuple(row)
        return None
        
    async def fetchall(self):
        """Возвращает все строки результата"""
        rows = await self.cursor.fetchall()
        return [tuple(row) for row in rows]
