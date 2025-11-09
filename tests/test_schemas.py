"""
Tests for Pydantic schemas
"""
import pytest
from pydantic import ValidationError

from bot.schemas.user import UserCreate, UserUpdate
from bot.schemas.liquidation_settings import (
    LiquidationSettingsCreate,
    LiquidationSettingsUpdate,
)


@pytest.mark.unit
class TestUserSchemas:
    """Tests for User schemas."""

    def test_user_create_valid(self):
        """Test creating a valid UserCreate."""
        user_data = {
            "id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en",
        }
        user = UserCreate(**user_data)
        assert user.id == 123456789
        assert user.username == "test_user"

    def test_user_create_minimal(self):
        """Test creating UserCreate with minimal data."""
        user_data = {"id": 123456789}
        user = UserCreate(**user_data)
        assert user.id == 123456789
        assert user.username == "" or user.username is None

    def test_user_create_missing_id(self):
        """Test that UserCreate requires id."""
        with pytest.raises(ValidationError):
            UserCreate(username="test")

    def test_user_update(self):
        """Test UserUpdate schema."""
        update_data = {"first_name": "Updated"}
        user_update = UserUpdate(**update_data)
        assert user_update.first_name == "Updated"


@pytest.mark.unit
class TestLiquidationSettingsSchemas:
    """Tests for LiquidationSettings schemas."""

    def test_liquidation_settings_create_valid(self):
        """Test creating valid LiquidationSettingsCreate."""
        settings_data = {
            "user_id": 123456789,
            "enabled": True,
            "threshold": 1000.0,
            "exchange": "binance",
            "pairs": ["BTCUSDT", "ETHUSDT"],
        }
        settings = LiquidationSettingsCreate(**settings_data)
        assert settings.user_id == 123456789
        assert settings.enabled is True
        assert settings.threshold == 1000.0
        assert settings.exchange == "binance"
        assert len(settings.pairs) == 2

    def test_liquidation_settings_create_defaults(self):
        """Test LiquidationSettingsCreate with defaults."""
        settings_data = {"user_id": 123456789}
        settings = LiquidationSettingsCreate(**settings_data)
        assert settings.enabled is False
        assert settings.threshold == 0.0
        assert settings.pairs == []

    def test_liquidation_settings_create_missing_user_id(self):
        """Test that LiquidationSettingsCreate requires user_id."""
        with pytest.raises(ValidationError):
            LiquidationSettingsCreate(enabled=True)

    def test_liquidation_settings_update(self):
        """Test LiquidationSettingsUpdate."""
        update_data = {"threshold": 5000.0, "pairs": ["BTCUSDT"]}
        settings_update = LiquidationSettingsUpdate(**update_data)
        assert settings_update.threshold == 5000.0
        assert settings_update.pairs == ["BTCUSDT"]

    def test_liquidation_settings_update_partial(self):
        """Test partial update of LiquidationSettings."""
        update_data = {"threshold": 3000.0}
        settings_update = LiquidationSettingsUpdate(**update_data)
        assert settings_update.threshold == 3000.0
        # Other fields should have defaults
        assert settings_update.pairs == []

