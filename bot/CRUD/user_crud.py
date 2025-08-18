from bot.models.user import UserDB
from bot.CRUD.base import CRUDBase
from bot.schemas.user import UserCreate, UserUpdate


class UserCRUD(CRUDBase[UserDB, UserCreate, UserUpdate]):
    pass


user = UserCRUD(UserDB)
