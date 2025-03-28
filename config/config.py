import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/bot.db')

# Admin Configuration
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '1152117246'))

# Bot Limits Configuration
FREE_TEXT_MESSAGES_LIMIT = int(os.getenv('FREE_TEXT_MESSAGES_LIMIT', 5))
FREE_IMAGE_GENERATION_LIMIT = int(os.getenv('FREE_IMAGE_GENERATION_LIMIT', 3))
FREE_VOICE_MESSAGES_LIMIT = int(os.getenv('FREE_VOICE_MESSAGES_LIMIT', 5))  # Same as text by default

# Daily free message settings
DAILY_FREE_MESSAGES = int(os.getenv('DAILY_FREE_MESSAGES', 1))

# Referral Reward
REFERRAL_REWARD_STARS = int(os.getenv('REFERRAL_REWARD_STARS', 10))

# Service costs in stars
TEXT_MESSAGE_STARS_COST = 2
IMAGE_GENERATION_STARS_COST = 5
VOICE_MESSAGE_STARS_COST = 3

# Check if required environment variables are set
def validate_config():
    missing_vars = []
    
    if not BOT_TOKEN:
        missing_vars.append('TELEGRAM_BOT_TOKEN')
    
    if not OPENAI_API_KEY:
        missing_vars.append('OPENAI_API_KEY')
    
    if not OPENAI_ASSISTANT_ID:
        missing_vars.append('OPENAI_ASSISTANT_ID')
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file.")
        return False
    
    return True
