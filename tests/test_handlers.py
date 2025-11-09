"""
Tests for bot handlers
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User, Chat, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers import base, liquidation
from bot.schemas.user import UserCreate


@pytest.mark.asyncio
@pytest.mark.unit
class TestBaseHandlers:
    """Tests for base handlers."""

    async def test_cmd_start_new_user(
        self, mock_message, db_session: AsyncSession
    ):
        """Test /start command with a new user."""
        from bot import CRUD
        
        # Ensure user doesn't exist
        existing_user = await CRUD.user.get(db_session, id=mock_message.from_user.id)
        if existing_user:
            await CRUD.user.delete(db_session, id=existing_user.id)
            await db_session.commit()
        
        # Call handler
        await base.cmd_start(mock_message, db_session, mock_message.from_user)
        
        # Verify user was created
        user = await CRUD.user.get(db_session, id=mock_message.from_user.id)
        assert user is not None
        assert user.id == mock_message.from_user.id
        
        # Verify message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Hello" in call_args
        assert str(user.id) in call_args

    async def test_cmd_start_existing_user(
        self, mock_message, db_session: AsyncSession, test_user
    ):
        """Test /start command with an existing user."""
        # Set user ID to match test_user
        mock_message.from_user.id = test_user.id
        
        await base.cmd_start(mock_message, db_session, mock_message.from_user)
        
        # Verify message was sent
        mock_message.answer.assert_called_once()

    async def test_cmd_help(self, mock_message):
        """Test /help command."""
        mock_message.text = "/help"
        
        await base.cmd_help(mock_message, mock_message.from_user)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Help" in str(call_args) or "commands" in str(call_args).lower()

    async def test_cmd_stop(self, mock_message, db_session: AsyncSession, test_user):
        """Test /stop command."""
        mock_message.from_user.id = test_user.id
        mock_message.text = "/stop"
        
        await base.cmd_stop(mock_message, db_session, mock_message.from_user)
        
        # Verify user was deleted
        from bot import CRUD
        user = await CRUD.user.get(db_session, id=test_user.id)
        assert user is None
        
        # Verify message was sent
        mock_message.answer.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiquidationHandlers:
    """Tests for liquidation handlers."""

    async def test_cmd_set_monitor(self, mock_message, db_session: AsyncSession):
        """Test /setup_lm command."""
        from aiogram.fsm.context import FSMContext
        
        mock_message.text = "/setup_lm"
        mock_state = MagicMock(spec=FSMContext)
        mock_state.set_state = AsyncMock()
        
        await liquidation.cmd_set_monitor(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        mock_state.set_state.assert_called_once()

    async def test_cmd_show_lm_settings(
        self, mock_message, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test /show_lm_settings command."""
        from bot.models.user import UserDB
        
        # Create user with settings
        user_db = await db_session.get(UserDB, test_liquidation_settings.user_id)
        mock_message.from_user.id = user_db.id
        
        await liquidation.cmd_show_liquidation_monitor_settings(
            mock_message, db_session, user_db
        )
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "settings" in call_args.lower() or "exchange" in call_args.lower()

    async def test_cmd_set_threshold(
        self, mock_message, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test /set_threshold command."""
        from bot.models.user import UserDB
        
        user_db = await db_session.get(UserDB, test_liquidation_settings.user_id)
        mock_message.from_user.id = user_db.id
        mock_message.text = "/set_threshold 5000"
        
        await liquidation.cmd_set_threshold(mock_message, db_session, user_db)
        
        # Verify threshold was updated
        await db_session.refresh(test_liquidation_settings)
        assert test_liquidation_settings.threshold == 5000.0
        
        mock_message.answer.assert_called_once()

    async def test_cmd_set_pairs(
        self, mock_message, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test /set_pairs command."""
        from bot.models.user import UserDB
        
        user_db = await db_session.get(UserDB, test_liquidation_settings.user_id)
        mock_message.from_user.id = user_db.id
        mock_message.text = "/set_pairs BTCUSDT, ETHUSDT, SOLUSDT"
        
        await liquidation.cmd_set_pairs(mock_message, db_session, user_db)
        
        # Verify pairs were updated
        await db_session.refresh(test_liquidation_settings)
        assert len(test_liquidation_settings.pairs) == 3
        assert "SOLUSDT" in test_liquidation_settings.pairs
        
        mock_message.answer.assert_called_once()

