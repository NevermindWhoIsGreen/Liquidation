from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db_session_maker: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.db_session_maker: async_sessionmaker[AsyncSession] = db_session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.db_session_maker() as session:
            data["db"] = session
            return await handler(event, data)
