from pydantic import BaseModel


class User(BaseModel):
    username: str | None = ""
    first_name: str | None = ""
    last_name: str | None = ""
    language_code: str | None = ""


class UserCreate(User):
    id: int


class UserUpdate(User):
    pass


class UserRead(UserCreate):
    model_config = {"extra": "forbid"}
