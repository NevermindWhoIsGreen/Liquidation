from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func

from bot.db.base_class import Base


if TYPE_CHECKING:
    from bot.models.liquid_monitor_settings import LiquidMonitorSettingsDB



class UserDB(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    liquid_monitor_settings: Mapped["LiquidMonitorSettingsDB"] = relationship(
        back_populates="user"
    )