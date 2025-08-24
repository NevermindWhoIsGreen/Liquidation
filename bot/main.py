import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config.base import settings
from bot.handlers import base, liquidation
from bot.db.connection import db_session_maker
from bot.middlewares.db_session_middleware import DbSessionMiddleware
from bot.middlewares.user_middleware import UserMiddleware
from bot.services.liquidation_monitor import start_handler


logging.basicConfig(level=logging.INFO)

bot: Bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
dp: Dispatcher = Dispatcher()



async def main(bot: Bot) -> None:
    asyncio.create_task(start_handler(bot))

    dp.update.middleware.register(DbSessionMiddleware(db_session_maker=db_session_maker))
    dp.message.middleware.register(UserMiddleware())
    dp.callback_query.middleware.register(UserMiddleware())
    dp.include_routers(base.router, liquidation.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot) # type: ignore


if __name__ == "__main__":
    asyncio.run(main(bot))
