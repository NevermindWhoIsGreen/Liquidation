# Liquidation Monitor Bot

This project is a Telegram bot designed to send real-time notifications about account liquidations on cryptocurrency exchanges (Binance, OKX, BitMEX).

## Features

- Real-time liquidation monitoring from multiple exchanges
- Customizable thresholds and trading pairs
- User-specific notification settings
- PostgreSQL database for data persistence

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))

### Setup

1. **Create a `.env` file** in the project root:

```bash
# Telegram Bot Token (required)
BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration (optional - defaults shown)
DATABASE_USER=liquidation_user
DATABASE_PASSWORD=liquidation_pass
DATABASE_DB=liquidation_db
# Note: DATABASE_EXTERNAL_PORT is for accessing DB from host (default: 5433)
# The bot connects internally, so this is only needed for external tools
```

2. **Run with Docker Compose** (one command):

```bash
docker-compose up --build
```

This will:
- Build the bot Docker image
- Start PostgreSQL database
- Run database migrations automatically
- Start the Telegram bot

### Docker Commands

- **Start in background**: `docker-compose up -d`
- **View logs**: `docker-compose logs -f bot`
- **Stop**: `docker-compose down`
- **Stop and remove volumes**: `docker-compose down -v`
- **Rebuild**: `docker-compose up --build`

## Manual Setup (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database and configure `.env` file

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the bot:
```bash
python -m bot.main
```

## Bot Commands

- `/start` - Start the bot and register
- `/help` - Show available commands
- `/setup_lm` - Interactive setup for liquidation monitor
- `/start_lm` / `/stop_lm` - Enable/disable monitoring
- `/set_threshold` - Update minimum liquidation amount
- `/set_pairs` - Update trading pairs to monitor
- `/show_lm_settings` - Display current settings
- `/drop_lm_settings` - Delete monitoring settings
- `/stop` - Unsubscribe and delete user data

## Supported Exchanges

- Binance Futures
- OKX Futures
- BitMEX

## Project Structure

```
bot/
├── config/          # Configuration settings
├── models/          # Database models
├── schemas/         # Pydantic schemas
├── CRUD/            # Database operations
├── handlers/        # Telegram bot handlers
├── middlewares/     # Middleware components
├── services/        # Business logic (liquidation monitoring)
└── db/              # Database connection
``` 
