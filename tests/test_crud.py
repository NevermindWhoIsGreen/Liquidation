"""
Tests for CRUD operations
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot import CRUD
from bot.schemas.user import UserCreate, UserUpdate
from bot.schemas.liquidation_settings import (
    LiquidationSettingsCreate,
    LiquidationSettingsUpdate,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestUserCRUD:
    """Tests for User CRUD operations."""

    async def test_create_user(self, db_session: AsyncSession, sample_user_data):
        """Test creating a new user."""
        user_create = UserCreate(**sample_user_data)
        user = await CRUD.user.create(db_session, obj_in=user_create)
        
        assert user.id == sample_user_data["id"]
        assert user.username == sample_user_data["username"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]
        assert user.language_code == sample_user_data["language_code"]

    async def test_get_user(self, db_session: AsyncSession, test_user):
        """Test retrieving a user by ID."""
        user = await CRUD.user.get(db_session, id=test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    async def test_get_user_not_found(self, db_session: AsyncSession):
        """Test retrieving a non-existent user."""
        user = await CRUD.user.get(db_session, id=999999999)
        assert user is None

    async def test_update_user(self, db_session: AsyncSession, test_user):
        """Test updating a user."""
        update_data = UserUpdate(first_name="Updated", last_name="Name")
        updated_user = await CRUD.user.update(
            db_session, db_obj=test_user, obj_in=update_data
        )
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.id == test_user.id  # ID should not change

    async def test_delete_user(self, db_session: AsyncSession, test_user):
        """Test deleting a user."""
        user_id = test_user.id
        deleted_user = await CRUD.user.delete(db_session, id=user_id)
        
        assert deleted_user is not None
        assert deleted_user.id == user_id
        
        # Verify user is deleted
        user = await CRUD.user.get(db_session, id=user_id)
        assert user is None

    async def test_get_multi_users(self, db_session: AsyncSession):
        """Test retrieving multiple users."""
        # Create multiple users
        users_data = [
            {"id": 111, "username": "user1", "first_name": "User", "last_name": "One"},
            {"id": 222, "username": "user2", "first_name": "User", "last_name": "Two"},
            {"id": 333, "username": "user3", "first_name": "User", "last_name": "Three"},
        ]
        
        for user_data in users_data:
            user_create = UserCreate(**user_data)
            await CRUD.user.create(db_session, obj_in=user_create)
        
        await db_session.commit()
        
        # Get all users - use a condition that's always true
        from sqlalchemy import true
        users = await CRUD.user.get_multi(
            db_session, where_conditions=[true()]  # Get all
        )
        
        assert len(users) >= 3


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiquidationSettingsCRUD:
    """Tests for LiquidationSettings CRUD operations."""

    async def test_create_liquidation_settings(
        self, db_session: AsyncSession, test_user, sample_liquidation_settings_data
    ):
        """Test creating liquidation settings."""
        settings_create = LiquidationSettingsCreate(**sample_liquidation_settings_data)
        settings = await CRUD.liquidation_settings.create(
            db_session, obj_in=settings_create
        )
        
        assert settings.user_id == sample_liquidation_settings_data["user_id"]
        assert settings.enabled == sample_liquidation_settings_data["enabled"]
        assert settings.threshold == sample_liquidation_settings_data["threshold"]
        assert settings.exchange == sample_liquidation_settings_data["exchange"]
        assert settings.pairs == sample_liquidation_settings_data["pairs"]

    async def test_get_by_user_id(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test retrieving settings by user ID."""
        settings = await CRUD.liquidation_settings.get_by_user_id(
            db_session, user_id=test_liquidation_settings.user_id
        )
        
        assert settings is not None
        assert settings.user_id == test_liquidation_settings.user_id

    async def test_get_by_user_id_not_found(self, db_session: AsyncSession):
        """Test retrieving settings for non-existent user."""
        settings = await CRUD.liquidation_settings.get_by_user_id(
            db_session, user_id=999999999
        )
        assert settings is None

    async def test_toggle_monitor(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test toggling monitor on/off."""
        # Turn off
        settings = await CRUD.liquidation_settings.toggle_monitor(
            db_session, user_id=test_liquidation_settings.user_id, turn_on=False
        )
        assert settings.enabled is False
        
        # Turn on
        settings = await CRUD.liquidation_settings.toggle_monitor(
            db_session, user_id=test_liquidation_settings.user_id, turn_on=True
        )
        assert settings.enabled is True

    async def test_update_liquidation_settings(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test updating liquidation settings."""
        update_data = LiquidationSettingsUpdate(
            threshold=5000.0, pairs=["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        )
        updated_settings = await CRUD.liquidation_settings.update(
            db_session, db_obj=test_liquidation_settings, obj_in=update_data
        )
        
        assert updated_settings.threshold == 5000.0
        assert len(updated_settings.pairs) == 3
        assert "SOLUSDT" in updated_settings.pairs

    async def test_get_multi_enabled_settings(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test retrieving multiple enabled settings."""
        from bot.models.liquid_monitor_settings import LiquidMonitorSettingsDB
        
        enabled_settings = await CRUD.liquidation_settings.get_multi(
            db_session,
            where_conditions=[LiquidMonitorSettingsDB.enabled.is_(True)],
        )
        
        assert len(enabled_settings) >= 1
        assert all(s.enabled for s in enabled_settings)

