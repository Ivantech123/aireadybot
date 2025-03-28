from psycopg_pool import AsyncConnectionPool
from typing import List, Tuple, Dict
import logging

class DatabaseError(Exception):
    def __init__(self, msg: str = "Error"):
        self.msg=msg
    def output(self):
        logging.error("Database error:", self.msg)

class DataBase:
    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool
    async def create_tables(self):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, chatgpt INT, dall_e INT, stable_diffusion INT, midjourney INT, referrer_id BIGINT)")
                    await cursor.execute("CREATE TABLE IF NOT EXISTS orders (invoice_id INT PRIMARY KEY, user_id BIGINT, product TEXT, FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)")
                    await cursor.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, user_id BIGINT, role TEXT, content TEXT, tokens INT, FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)")
                    
                    # Новые таблицы для подписок и реферальной системы
                    await cursor.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY, 
                        user_id BIGINT, 
                        type TEXT, 
                        plan TEXT, 
                        daily_limit INT, 
                        start_date TIMESTAMP, 
                        end_date TIMESTAMP,
                        usage_today INT DEFAULT 0,
                        last_usage_reset TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)
                    """)
                    
                    await cursor.execute("""CREATE TABLE IF NOT EXISTS referrals (
                        id SERIAL PRIMARY KEY, 
                        referrer_id BIGINT, 
                        referred_id BIGINT, 
                        date_joined TIMESTAMP,
                        bonus_given BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (referrer_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        FOREIGN KEY (referred_id) REFERENCES users (user_id) ON DELETE CASCADE)
                    """)
                    
                    # Таблица для администраторов
                    await cursor.execute("""CREATE TABLE IF NOT EXISTS admins (
                        user_id BIGINT PRIMARY KEY,
                        role TEXT,
                        added_date TIMESTAMP)
                    """)
                    
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def is_user(self, user_id: int) -> Tuple[int]:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id, ))
                    result = await cursor.fetchone()
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def insert_user(self, user_id: int, referrer_id: int = None):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("INSERT INTO users(user_id, chatgpt, dall_e, stable_diffusion, midjourney, referrer_id) VALUES (%s, %s, %s, %s, %s, %s)", (user_id, 3000, 3, 3, 3, referrer_id))
                    # Если это реферал, добавляем запись в таблицу referrals
                    if referrer_id is not None:
                        await cursor.execute("INSERT INTO referrals(referrer_id, referred_id, date_joined) VALUES (%s, %s, NOW())", (referrer_id, user_id))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_chatgpt(self, user_id: int) -> int:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT chatgpt FROM users WHERE user_id = %s", (user_id, ))
                    result = (await cursor.fetchone())[0]
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def set_chatgpt(self, user_id: int, result: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET chatgpt = %s WHERE user_id = %s", (result, user_id))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_dalle(self, user_id: int) -> int:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT dall_e FROM users WHERE user_id = %s", (user_id, ))
                    result = (await cursor.fetchone())[0]
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def set_dalle(self, user_id: int, result: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET dall_e = %s WHERE user_id = %s", (result, user_id))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_stable(self, user_id: int) -> int:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT stable_diffusion FROM users WHERE user_id = %s", (user_id, ))
                    result = (await cursor.fetchone())[0]
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def set_stable(self, user_id: int, result: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET stable_diffusion = %s WHERE user_id = %s", (result, user_id))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_userinfo(self, user_id: int) -> Tuple[int, int, int, int]:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT chatgpt, dall_e, stable_diffusion, midjourney FROM users WHERE user_id = %s", (user_id, ))
                    result = await cursor.fetchone()
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def new_order(self, invoice_id: int, user_id: int, product: str):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("INSERT INTO orders(invoice_id, user_id, product) VALUES (%s, %s, %s)", (invoice_id, user_id, product))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_orderdata(self, invoice_id: int) -> Tuple[int, str]:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT user_id, product FROM orders WHERE invoice_id = %s", (invoice_id, ))
                    result = await cursor.fetchone()
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def update_chatgpt(self, user_id: int, invoice_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET chatgpt = chatgpt + 100000 WHERE user_id = %s", (user_id, ))
                    await cursor.execute("DELETE FROM orders WHERE invoice_id = %s", (invoice_id, ))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def update_dalle(self, user_id: int, invoice_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET dall_e = dall_e + 50 WHERE user_id = %s", (user_id, ))
                    await cursor.execute("DELETE FROM orders WHERE invoice_id = %s", (invoice_id, ))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def update_stable(self, user_id: int, invoice_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET stable_diffusion = stable_diffusion + 50 WHERE user_id = %s", (user_id, ))
                    await cursor.execute("DELETE FROM orders WHERE invoice_id = %s", (invoice_id, ))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def save_message(self, user_id: int, role: str, message: str, tokens: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("INSERT INTO messages(user_id, role, content, tokens) VALUES (%s, %s, %s, %s)", (user_id, role, message, tokens))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def delete_messages(self, user_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("DELETE FROM messages WHERE user_id = %s", (user_id,))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_messages(self, user_id: int) -> Tuple[List[Dict[str, str]], int]:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                    WITH cte AS (
                        SELECT 
                            id, 
                            role, 
                            content, 
                            tokens,
                            SUM(tokens) OVER (ORDER BY id DESC) AS tokens_total
                        FROM messages
                        WHERE user_id = %s
                    )
                    SELECT role, content, tokens_total
                    FROM cte
                    WHERE tokens_total <= 128000
                    ORDER BY id ASC;""", (user_id,))
                    result = await cursor.fetchall()
                    if not result:
                        return [], 0
                    return [{"role": role, "content": content}  for role, content, _ in result], result[0][2]
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    async def get_midjourney(self, user_id: int) -> int:
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT midjourney FROM users WHERE user_id = %s", (user_id, ))
                    result = (await cursor.fetchone())[0]
                    return result
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
            
    async def set_midjourney(self, user_id: int, result: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET midjourney = %s WHERE user_id = %s", (result, user_id))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
            
    async def update_midjourney(self, user_id: int, invoice_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("UPDATE users SET midjourney = midjourney + 50 WHERE user_id = %s", (user_id, ))
                    if invoice_id > 0:
                        await cursor.execute("DELETE FROM orders WHERE invoice_id = %s", (invoice_id, ))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def create_subscription(self, user_id: int, sub_type: str, plan: str, daily_limit: int, duration_days: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    # Проверяем, есть ли уже активная подписка этого типа
                    await cursor.execute("SELECT id FROM subscriptions WHERE user_id = %s AND type = %s AND end_date > NOW()", (user_id, sub_type))
                    existing = await cursor.fetchone()
                    
                    if existing:
                        # Если подписка уже есть, обновляем ее
                        await cursor.execute("""
                            UPDATE subscriptions 
                            SET plan = %s, daily_limit = %s, start_date = NOW(), 
                                end_date = NOW() + INTERVAL '%s days', usage_today = 0, last_usage_reset = NOW()
                            WHERE user_id = %s AND type = %s AND end_date > NOW()
                        """, (plan, daily_limit, duration_days, user_id, sub_type))
                    else:
                        # Создаем новую подписку
                        await cursor.execute("""
                            INSERT INTO subscriptions(user_id, type, plan, daily_limit, start_date, end_date, usage_today, last_usage_reset)
                            VALUES (%s, %s, %s, %s, NOW(), NOW() + INTERVAL '%s days', 0, NOW())
                        """, (user_id, sub_type, plan, daily_limit, duration_days))
                    
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def check_subscription(self, user_id: int, sub_type: str):
        """Проверяет активную подписку и возвращает информацию о ней"""
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT plan, daily_limit, start_date, end_date, usage_today, last_usage_reset 
                        FROM subscriptions 
                        WHERE user_id = %s AND type = %s AND end_date > NOW()
                    """, (user_id, sub_type))
                    result = await cursor.fetchone()
                    
                    if not result:
                        return None
                        
                    # Проверяем, нужно ли сбросить счетчик использования на сегодня
                    last_reset = result[5].date()
                    import datetime
                    today = datetime.datetime.now().date()
                    
                    if last_reset < today:
                        # Сбрасываем счетчик, если прошел день
                        await cursor.execute("""
                            UPDATE subscriptions 
                            SET usage_today = 0, last_usage_reset = NOW() 
                            WHERE user_id = %s AND type = %s AND end_date > NOW()
                        """, (user_id, sub_type))
                        await conn.commit()
                        return {'plan': result[0], 'daily_limit': result[1], 'start_date': result[2], 'end_date': result[3], 'usage_today': 0}
                    
                    return {'plan': result[0], 'daily_limit': result[1], 'start_date': result[2], 'end_date': result[3], 'usage_today': result[4]}
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def increment_subscription_usage(self, user_id: int, sub_type: str):
        """Увеличивает счетчик использования подписки на день"""
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE subscriptions 
                        SET usage_today = usage_today + 1 
                        WHERE user_id = %s AND type = %s AND end_date > NOW()
                    """, (user_id, sub_type))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def get_referrals(self, user_id: int):
        """Получает список рефералов пользователя"""
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT r.referred_id, r.date_joined, r.bonus_given 
                        FROM referrals r 
                        WHERE r.referrer_id = %s
                    """, (user_id,))
                    return await cursor.fetchall()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def give_referral_bonus(self, referrer_id: int, referred_id: int, chatgpt_bonus: int = 5000, dalle_bonus: int = 5, stable_bonus: int = 5, midjourney_bonus: int = 5):
        """Выдает бонус реферреру за приглашенного пользователя"""
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    # Проверяем, что бонус еще не был выдан
                    await cursor.execute("SELECT bonus_given FROM referrals WHERE referrer_id = %s AND referred_id = %s", (referrer_id, referred_id))
                    result = await cursor.fetchone()
                    
                    if result and not result[0]:
                        # Выдаем бонус
                        await cursor.execute("""
                            UPDATE users 
                            SET chatgpt = chatgpt + %s, 
                                dall_e = dall_e + %s, 
                                stable_diffusion = stable_diffusion + %s,
                                midjourney = midjourney + %s 
                            WHERE user_id = %s
                        """, (chatgpt_bonus, dalle_bonus, stable_bonus, midjourney_bonus, referrer_id))
                        
                        # Отмечаем, что бонус выдан
                        await cursor.execute("UPDATE referrals SET bonus_given = TRUE WHERE referrer_id = %s AND referred_id = %s", (referrer_id, referred_id))
                        await conn.commit()
                        return True
                    return False
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
            
    async def add_admin(self, user_id: int, role: str = "admin"):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO admins(user_id, role, added_date) 
                        VALUES (%s, %s, NOW()) 
                        ON CONFLICT (user_id) DO UPDATE 
                        SET role = EXCLUDED.role, added_date = NOW()
                    """, (user_id, role))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def remove_admin(self, user_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
                    await conn.commit()
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err
    
    async def is_admin(self, user_id: int):
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT role FROM admins WHERE user_id = %s", (user_id,))
                    result = await cursor.fetchone()
                    return result[0] if result else None
        except Exception as e:
            err = DatabaseError(str(e))
            err.output()
            raise err