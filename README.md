<<<<<<< HEAD
# ChatGPT, DALL·E, Stable Diffusion Telegram bot

## Table of Contents

+ [Start](#start)
+ [ChatGPT](#chatgpt)
+ [DALL·E](#dalle)
+ [Stable Diffusion](#stablediffusion)
+ [Account and buy](#accountbuy)
+ [Tests](#tests)
+ [Variables](#variables)
+ [Database](#database)
+ [How to deploy](#howtodeploy)
+ [License](#license)

## Start <a name = "start"></a>
When the user enters the start command, the bot sends him a welcome message stating that the user has free 3000 ChatGPT tokens, 3 DALL·E image generations and 3 Stable Diffusion image generations and displays 4 buttons: "💭Chatting — ChatGPT-4o", "🌄Image generation — DALL·E 3", "🌅Image generation — Stable Diffusion 3" and "👤My account | 💰Buy". If the user is already registered, the bot only displays buttons.

![gif](images/start.gif)

## ChatGPT <a name = "chatgpt"></a>
If the user wants to chat with ChatGPT, he presses the "💭Chatting — ChatGPT" button and chats.

This bot saves the context of the dialogue!

![gif](images/chatgpt.gif)

In [openaitools.py](app/services/openaitools.py) in the OpenAiTools class there are three parameters in the get_chatgpt function:

```model``` - The model which is used for generation.

```max_tokens``` - The maximum number of tokens that can be generated in the chat completion.

```temperature``` - What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.

## DALL·E <a name = "dalle"></a>
If the user wants to generate image with DALL·E, he presses the "🌄Image generation — DALL·E" button and generates.

![gif](images/dalle.gif)

Generated image:

![image](images/dalle.png)

In [openaitools.py](app/services/openaitools.py) in the OpenAiTools class there are three parameters in the get_dalle function:

```model``` - The model which is used for generation.

```n``` - The number of images to generate. Must be between 1 and 10.

```size``` - The size of the generated images. Must be one of 256x256, 512x512, or 1024x1024.

## Stable Diffusion <a name = "stablediffusion"></a>
If the user wants to generate image with Stable Diffusion, he presses the "🌅Image generation — Stable Diffusion" button and generates.

![gif](images/stable.gif)

Generated image:

![image](images/stable.png)

In [stablediffusion.py](app/services/stablediffusion.py) there is one parameter:

```model``` - The model to use for generation: sd3-medium requires 3.5 credits per generation, sd3-large requires 6.5 credits per generation, sd3-large-turbo requires 4 credits per generation.

## Account and buy <a name = "accountbuy"></a>
If the user wants to see account information or buy tokens and generations, he presses the "👤My account | 💰Buy" button. After pressing the button, the bot displays information about the rest of the user's ChatGPT tokens, DALL·E image generations and Stable Diffusion image generations. If the user wants to buy tokens and generations, he presses the "💰Buy tokens and generations" button, selects the product and currency. After that, the user needs to press the "💰Buy" button and pay in Crypto Bot if he wants to pay. If the user has paid, he should press "☑️Check" button and tokens or image generations will be added to his account. If the user hasn't paid, the bot will display the message "⌚️We have not received payment yet".

Payments are processed via webhooks (webhook url is specified in [Crypto Bot](https://t.me/send)).

![gif](images/buy.gif)

## Tests <a name = "tests"></a>

Unit tests are located in [tests folder](tests).

Coverage 91%:

![img.png](images/img.png)

## Variables<a name = "variables"></a>

All variables: 

```OPENAI_API_KEY``` - OpenAI API key

```STABLE_DIFFUSION_API_KEY``` - Stable Diffusion API key

```TELEGRAM_BOT_TOKEN``` - Telegram Bot API key

```CRYPTOPAY_KEY``` - [Crypto Bot](https://t.me/send) API key

```BASE_WEBHOOK_URL``` - Server URL

```DATABASE_URL``` - Database URL

## Database <a name = "database"></a>

This project requires PostgreSQL database with two tables: users(user_id, username, chatgpt, dall_e, stable_diffusion), orders(invoice_id, user_id, product) and messages(id, user_id, role, content, messages). 

Users and information about them will be added to the "users" table, orders will be added to the "orders" table and ChatGPT context window messages will be added to the "messages" table.

```DATABASE_URL``` - database url.

## How to deploy <a name = "howtodeploy"></a>

This project can be easily deployed on the [Railway](https://railway.app/) (if all variables are passed here and a Postgres database is created, BASE_WEBHOOK_URL is a free URL from Railway).

It can be also deployed via [docker-compose.yml](docker-compose.yml) if all variables are passed into the [.env](.env) file.
```BASE_WEBHOOK_URL``` in this case can be obtained via ngrok.

## License <a name = "license"></a>

[License](https://github.com/vladislav-bordiug/ChatGPT_DALL_E_StableDiffusion_Telegram_Bot/blob/main/LICENSE) - this project is licensed under Apache-2.0 license.
=======
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
>>>>>>> c0f76da98b0f8642c1bc97e2c9e2850a4a4cedb6
