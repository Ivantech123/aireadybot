import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management for the application"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Ensure environment variables are loaded
        load_dotenv()
        
        # Telegram configuration
        self._config['TELEGRAM_BOT_TOKEN'] = os.getenv('TELEGRAM_BOT_TOKEN')
        self._config['TELEGRAM_API_ID'] = os.getenv('TELEGRAM_API_ID')
        self._config['TELEGRAM_API_HASH'] = os.getenv('TELEGRAM_API_HASH')
        
        # OpenAI configuration
        self._config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        self._config['OPENAI_ASSISTANT_ID'] = os.getenv('OPENAI_ASSISTANT_ID')
        
        # Admin configuration
        self._config['ADMIN_USERNAME'] = os.getenv('ADMIN_USERNAME')
        self._config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD')
        
        # Payment configuration
        self._config['LAVA_API_KEY'] = os.getenv('LAVA_API_KEY')
        self._config['LAVA_SHOP_ID'] = os.getenv('LAVA_SHOP_ID')
        
        # Service costs
        self._config['TEXT_MESSAGE_STARS_COST'] = int(os.getenv('TEXT_MESSAGE_STARS_COST', '1'))
        self._config['VOICE_MESSAGE_STARS_COST'] = int(os.getenv('VOICE_MESSAGE_STARS_COST', '2'))
        self._config['IMAGE_GENERATION_STARS_COST'] = int(os.getenv('IMAGE_GENERATION_STARS_COST', '5'))
        
        # Free limits
        self._config['FREE_TEXT_MESSAGES_LIMIT'] = int(os.getenv('FREE_TEXT_MESSAGES_LIMIT', '5'))
        self._config['FREE_VOICE_MESSAGES_LIMIT'] = int(os.getenv('FREE_VOICE_MESSAGES_LIMIT', '3'))
        self._config['FREE_IMAGE_GENERATION_LIMIT'] = int(os.getenv('FREE_IMAGE_GENERATION_LIMIT', '2'))
        self._config['DAILY_FREE_MESSAGES'] = int(os.getenv('DAILY_FREE_MESSAGES', '3'))
        
        # Referral rewards
        self._config['REFERRAL_REWARD_STARS'] = int(os.getenv('REFERRAL_REWARD_STARS', '10'))
        
        # Validate critical configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate critical configuration settings"""
        critical_vars = [
            'TELEGRAM_BOT_TOKEN',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = [var for var in critical_vars if not self._config.get(var)]
        
        if missing_vars:
            logger.error(f"Missing critical environment variables: {', '.join(missing_vars)}")
            logger.error("Please set these variables in your .env file or environment.")
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value (for runtime changes)"""
        self._config[key] = value
        return value

# Create a singleton instance
config = ConfigManager()
