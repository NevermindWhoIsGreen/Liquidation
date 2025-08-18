from aiogram.filters import BaseFilter
from aiogram.types import Message, User


class UserFilter(BaseFilter):
    async def __call__(self, message: Message) -> dict[str, User] | bool:
        if message.from_user:
            return {"user": message.from_user}
        return False
