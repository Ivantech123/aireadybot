import asyncio
import asyncpg
from dotenv import load_dotenv
import os

async def create_database():
    load_dotenv()
    
    # Get connection string but connect to default 'postgres' database
    database_url = os.getenv("DATABASE_URL")
    print(f"Using connection string: {database_url}")
    
    try:
        # Connect to the default 'postgres' database
        conn = await asyncpg.connect(database_url)
        print("Connected to PostgreSQL successfully!")
        
        # Check if telegram_bot database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            "telegram_bot"
        )
        
        if exists:
            print("Database 'telegram_bot' already exists.")
        else:
            # Create telegram_bot database
            # We need to use SQL directly since asyncpg doesn't have a method for this
            await conn.execute("CREATE DATABASE telegram_bot")
            print("Database 'telegram_bot' created successfully!")
        
        # Close the connection
        await conn.close()
        
        # Update .env file to use telegram_bot database
        new_db_url = database_url.replace('/postgres', '/telegram_bot')
        
        with open(".env", "r") as f:
            content = f.read()
        
        with open(".env", "w") as f:
            f.write(content.replace(database_url, new_db_url))
            
        print(f"Updated .env file with new connection string: {new_db_url}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_database())
