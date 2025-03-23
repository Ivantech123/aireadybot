# Telegram GPT Bot

A Telegram bot that provides AI-powered text responses, voice transcription, and image generation capabilities with subscription management and Telegram Stars integration.

## Optimizations and Features

### Session Management

- Implemented `session_utils.py` with context managers and decorators for proper session handling
- Fixed DetachedInstanceError issues by storing user IDs instead of database objects in handlers
- Added session scope management to ensure proper transaction handling

### Error Handling

- Created centralized `error_handler.py` utility with decorators for consistent error handling
- Added detailed logging with traceback information
- Implemented error handling decorators for Telegram handlers

### Configuration Management

- Developed `config_manager.py` to centralize environment variable management
- Added validation for critical settings
- Improved security by centralizing credential management

### Telegram Stars Integration

- Integrated official Telegram Stars system for payments
- Implemented multiple fallback methods for stars balance retrieval
- Added user-friendly purchase flow with clear instructions

### Code Structure Improvements

- Enhanced session management across all handlers
- Improved startup process with better error handling
- Added detailed logging throughout the application

## Setup and Configuration

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Telegram Bot Token
- Telegram API credentials (for Telegram Stars)
- OpenAI API key (for AI features)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Telegram API Credentials
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=26507863
TELEGRAM_API_HASH=5cb6d934943762a1702333ab205d1f54

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/dbname

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Bot Configuration
ADMIN_PASSWORD=your_admin_password
USE_TELEGRAM_STARS=True
TEXT_MESSAGE_STARS_COST=1
VOICE_MESSAGE_STARS_COST=2
IMAGE_GENERATION_STARS_COST=5
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the environment variables in `.env`
4. Run the bot: `python -m bot.main`

## Project Structure

```
telegram_gpt_bot/
├── bot/
│   ├── handlers/
│   │   ├── admin_handlers.py
│   │   ├── basic_handlers.py
│   │   ├── chat_handlers.py
│   │   ├── image_handlers.py
│   │   ├── subscription_handlers.py
│   │   └── telegram_stars_handlers.py
│   ├── keyboards/
│   │   └── keyboards.py
│   ├── services/
│   │   ├── admin_service.py
│   │   ├── openai_service.py
│   │   ├── payment_service.py
│   │   ├── subscription_service.py
│   │   ├── telegram_stars_service.py
│   │   └── user_service.py
│   ├── utils/
│   │   ├── config_manager.py
│   │   ├── error_handler.py
│   │   └── session_utils.py
│   └── main.py
├── database/
│   ├── db.py
│   └── models.py
├── config/
│   └── config.py
├── .env
├── requirements.txt
└── README.md
```

## Features

- **Text Responses**: Ask questions and receive AI-powered responses
- **Voice Transcription**: Send voice messages and get text responses
- **Image Generation**: Generate images based on text prompts
- **Subscription System**: Manage user subscriptions with different plans
- **Telegram Stars**: Use official Telegram Stars for payments
- **Admin Panel**: Manage users, broadcast messages, and configure settings
- **Referral System**: Invite friends and earn rewards

## Best Practices Implemented

- Proper session management to prevent DetachedInstanceError
- Centralized configuration management
- Comprehensive error handling and logging
- Secure credential management
- Clean code structure with separation of concerns
- Fallback mechanisms for API integrations
