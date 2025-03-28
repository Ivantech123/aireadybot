import asyncio
import os
from dotenv import load_dotenv
import asyncpg

async def test_connection():
    load_dotenv()
    
    # u041fu043eu043bu0443u0447u0430u0435u043c u0441u0442u0440u043eu043au0443 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u044f u0438u0437 .env
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL: {database_url}")
    
    # u041fu0440u043eu0431u0443u0435u043c u0432u0430u0440u0438u0430u043du0442u044b u043fu043eu0434u043au043bu044eu0447u0435u043du0438u044f
    connection_strings = [
        database_url,
        "postgresql://postgres@localhost:5432/telegram_bot",
        "postgresql://postgres:123@localhost:5432/telegram_bot",
        "postgresql://postgres:postgres@localhost:5432/telegram_bot",
        "postgresql://postgres:pgdbpass@localhost:5432/telegram_bot",
        "postgresql://postgres:@localhost:5432/telegram_bot"
    ]
    
    for conn_str in connection_strings:
        print(f"\nu041fu0440u043eu0431u0443u044e u043fu043eu0434u043au043bu044eu0447u0438u0442u044cu0441u044f u0441 {conn_str}")
        try:
            # u041fu0440u043eu0431u0443u0435u043c u043fu043eu0434u043au043bu044eu0447u0438u0442u044cu0441u044f u043a u0431u0430u0437u0435 u0434u0430u043du043du044bu0445
            conn = await asyncpg.connect(conn_str)
            print("u041fu043eu0434u043au043bu044eu0447u0435u043du0438u0435 u0443u0441u043fu0435u0448u043du043e!")
            
            # u041fu0440u043eu0432u0435u0440u044fu0435u043c, u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u043bu0438 u0431u0430u0437u0430 u0434u0430u043du043du044bu0445 telegram_bot
            db_exists = await conn.fetchval(
                "SELECT COUNT(*) FROM pg_database WHERE datname = $1", 
                "telegram_bot"
            )
            
            print(f"u0411u0430u0437u0430 u0434u0430u043du043du044bu0445 telegram_bot {'существует' if db_exists else 'не существует'}")
            
            # u0421u043eu0437u0434u0430u0435u043c u0431u0430u0437u0443 u0434u0430u043du043du044bu0445, u0435u0441u043bu0438 u043eu043du0430 u043du0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442
            if not db_exists:
                # u041du0435u043eu0431u0445u043eu0434u0438u043cu043e u0438u0441u043fu043eu043bu044cu0437u043eu0432u0430u0442u044c u043au043eu043cu0430u043du0434u0443 SQL
                await conn.execute("CREATE DATABASE telegram_bot")
                print("u0411u0430u0437u0430 u0434u0430u043du043du044bu0445 telegram_bot u0441u043eu0437u0434u0430u043du0430!")
            
            # u0417u0430u043au0440u044bu0432u0430u0435u043c u0441u043eu0435u0434u0438u043du0435u043du0438u0435
            await conn.close()
            
            # u0415u0441u043bu0438 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u0435 u0443u0441u043fu0435u0448u043du043e, u043eu0431u043du043eu0432u043bu044fu0435u043c .env u0444u0430u0439u043b
            with open(".env", "r") as f:
                env_content = f.read()
            
            # u0417u0430u043cu0435u043du044fu0435u043c u0441u0442u0440u043eu043au0443 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u044f u043du0430 u0440u0430u0431u043eu0447u0443u044e
            env_content = env_content.replace(database_url, conn_str)
            
            with open(".env", "w") as f:
                f.write(env_content)
            
            print(f"u0424u0430u0439u043b .env u043eu0431u043du043eu0432u043bu0435u043d u0441 u0440u0430u0431u043eu0447u0435u0439 u0441u0442u0440u043eu043au043eu0439 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u044f: {conn_str}")
            
            # u0412u044bu0445u043eu0434u0438u043c u0438u0437 u0446u0438u043au043bu0430, u0442u0430u043a u043au0430u043a u0443u0436u0435 u043du0430u0448u043bu0438 u0440u0430u0431u043eu0447u0435u0435 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u0435
            break
        except Exception as e:
            print(f"u041eu0448u0438u0431u043au0430 u043fu043eu0434u043au043bu044eu0447u0435u043du0438u044f: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
