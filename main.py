import asyncio
import sys
from app.application import run

if __name__ == '__main__':
    # Исправление для Windows, чтобы psycopg мог работать с asyncio
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run()