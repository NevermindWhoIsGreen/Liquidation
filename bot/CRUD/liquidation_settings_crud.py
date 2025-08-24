from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.exceptions.exceptions import NotFoundError
from bot.models.liquid_monitor_settings import LiquidMonitorSettingsDB
from bot.CRUD.base import CRUDBase
from bot.schemas.liquidation_settings import (
    LiquidationSettingsCreate,
    LiquidationSettingsUpdate,
)


class LiquidSettingsCRUD(
    CRUDBase[
        LiquidMonitorSettingsDB, LiquidationSettingsCreate, LiquidationSettingsUpdate
    ]
):
    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> LiquidMonitorSettingsDB | None:
        result = await db.execute(
            select(LiquidMonitorSettingsDB).where(
                LiquidMonitorSettingsDB.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def toggle_monitor(self, db: AsyncSession, user_id: int, turn_on: bool) -> LiquidMonitorSettingsDB:
        stmt = update(self.model).where(
            self.model.user_id==user_id
        ).values(enabled=turn_on).returning(self.model)
        settings = await db.scalar(stmt)
        if not settings:
            raise NotFoundError(f"No settings for user_id: {user_id}")
        return settings


liquidation_settings = LiquidSettingsCRUD(LiquidMonitorSettingsDB)
