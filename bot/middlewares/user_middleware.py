from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot import CRUD


class UserMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db = data["db"]
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user = await CRUD.user.get(db=db, id=event.from_user.id)
            data["user_db"] = user
        return await handler(event, data)
