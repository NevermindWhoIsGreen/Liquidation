from pydantic import BaseModel


class LiquidationSettings(BaseModel):
    enabled: bool = False
    threshold: float | None = 0.0
    exchange: str | None = ''
    pairs: list[str] = []


class LiquidationSettingsCreate(LiquidationSettings):
    user_id: int


class LiquidationSettingsUpdate(LiquidationSettings):
    pass


class LiquidationSettingsRead(LiquidationSettingsCreate):
    id: int
    user_id: int
    model_config = {"extra": "forbid"}
