from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # bot settings
    BOT_TOKEN: SecretStr

    # postgres settings
    DATABASE_USER: str
    DATABASE_DB: str
    DATABASE_PORT: int = 5432
    DATABASE_HOST: str = "localhost"
    DATABASE_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_DB}"


settings = Settings() # type: ignore