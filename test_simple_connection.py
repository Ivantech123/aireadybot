import asyncio
import os
from dotenv import load_dotenv
import asyncpg

async def test_connection():
    load_dotenv()
    
    # Get connection string from .env
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL: {database_url}")
    
    # Try different connection strings
    connection_strings = [
        database_url,
        "postgresql://postgres@localhost:5432/telegram_bot",
        "postgresql://postgres:123@localhost:5432/telegram_bot",
        "postgresql://postgres:postgres@localhost:5432/telegram_bot",
        "postgresql://postgres:admin@localhost:5432/telegram_bot",
        "postgresql://postgres:password@localhost:5432/telegram_bot",
        "postgresql://postgres:@localhost:5432/telegram_bot"
    ]
    
    for conn_str in connection_strings:
        print(f"\nTrying to connect with {conn_str}")
        try:
            # Try to connect to database
            conn = await asyncpg.connect(conn_str)
            print("Connection successful!")
            
            # Close connection
            await conn.close()
            
            # If connection is successful, update .env file
            with open(".env", "r") as f:
                env_content = f.read()
            
            # Replace connection string with working one
            env_content = env_content.replace(database_url, conn_str)
            
            with open(".env", "w") as f:
                f.write(env_content)
            
            print(f".env file updated with working connection string: {conn_str}")
            
            # Exit loop as we found a working connection
            break
        except Exception as e:
            print(f"Connection error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
