import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.base import settings

from bot.handlers import base
from bot.services.liquidation_monitor import start_handler


MIN_USDT = 1000

logging.basicConfig(level=logging.INFO)

bot: Bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
dp = Dispatcher()



async def main(bot: Bot) -> None:
    asyncio.create_task(start_handler(bot))

    dp.include_routers(
        base.router,
    )

    await dp.start_polling(bot) # type: ignore


if __name__ == "__main__":
    asyncio.run(main(bot))
