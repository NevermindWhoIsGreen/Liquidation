from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON, DateTime, String, func, ForeignKey

from bot.db.base_class import Base


if TYPE_CHECKING:
    from bot.models.user import UserDB


class LiquidMonitorSettingsDB(Base):
    __tablename__ = "liquid_monitor_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    threshold: Mapped[float] = mapped_column(default=0.0)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pairs: Mapped[list[str]] = mapped_column(JSON)

    user: Mapped["UserDB"] = relationship(back_populates="liquid_monitor_settings", uselist=False)