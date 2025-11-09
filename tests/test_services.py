"""
Tests for service layer (liquidation monitoring)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.liquidation_monitor.liquidation_starter import (
    get_active_liq_settings,
    process_liquidation,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiquidationMonitor:
    """Tests for liquidation monitoring service."""

    async def test_get_active_liq_settings(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test retrieving active liquidation settings."""
        # Ensure settings are enabled
        test_liquidation_settings.enabled = True
        await db_session.commit()
        
        # Mock db_session_maker
        from bot.db.connection import db_session_maker
        with patch("bot.services.liquidation_monitor.liquidation_starter.db_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__.return_value = db_session
            mock_maker.return_value.__aexit__ = AsyncMock()
            
            settings = await get_active_liq_settings()
            
            assert len(settings) >= 1
            assert all(s.enabled for s in settings)

    async def test_process_liquidation_with_match(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test processing liquidation that matches user criteria."""
        # Set up settings to match
        test_liquidation_settings.enabled = True
        test_liquidation_settings.threshold = 1000.0
        test_liquidation_settings.pairs = ["BTCUSDT"]
        test_liquidation_settings.exchange = "binance"
        await db_session.commit()
        
        mock_bot = MagicMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        liquidation_info = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "price": "50000",
            "quantity": "0.1",
            "link": "https://example.com",
        }
        
        # Mock get_active_liq_settings
        with patch(
            "bot.services.liquidation_monitor.liquidation_starter.get_active_liq_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = [test_liquidation_settings]
            
            await process_liquidation(mock_bot, "Binance", liquidation_info)
            
            # Verify message was sent (USD value = 50000 * 0.1 = 5000 > 1000 threshold)
            mock_bot.send_message.assert_called_once()
            call_args = mock_bot.send_message.call_args
            assert call_args[0][0] == test_liquidation_settings.user_id
            assert "Liquidation" in call_args[0][1]
            assert "BTCUSDT" in call_args[0][1]

    async def test_process_liquidation_below_threshold(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test processing liquidation below threshold."""
        test_liquidation_settings.enabled = True
        test_liquidation_settings.threshold = 10000.0  # High threshold
        test_liquidation_settings.pairs = ["BTCUSDT"]
        test_liquidation_settings.exchange = "binance"
        await db_session.commit()
        
        mock_bot = MagicMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        liquidation_info = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "price": "50000",
            "quantity": "0.1",  # USD value = 5000 < 10000 threshold
        }
        
        with patch(
            "bot.services.liquidation_monitor.liquidation_starter.get_active_liq_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = [test_liquidation_settings]
            
            await process_liquidation(mock_bot, "Binance", liquidation_info)
            
            # Should not send message (below threshold)
            mock_bot.send_message.assert_not_called()

    async def test_process_liquidation_wrong_pair(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test processing liquidation for wrong trading pair."""
        test_liquidation_settings.enabled = True
        test_liquidation_settings.threshold = 1000.0
        test_liquidation_settings.pairs = ["ETHUSDT"]  # Different pair
        test_liquidation_settings.exchange = "binance"
        await db_session.commit()
        
        mock_bot = MagicMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        liquidation_info = {
            "symbol": "BTCUSDT",  # Different symbol
            "side": "SELL",
            "price": "50000",
            "quantity": "0.1",
        }
        
        with patch(
            "bot.services.liquidation_monitor.liquidation_starter.get_active_liq_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = [test_liquidation_settings]
            
            await process_liquidation(mock_bot, "Binance", liquidation_info)
            
            # Should not send message (wrong pair)
            mock_bot.send_message.assert_not_called()

    async def test_process_liquidation_wrong_exchange(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test processing liquidation from wrong exchange."""
        test_liquidation_settings.enabled = True
        test_liquidation_settings.threshold = 1000.0
        test_liquidation_settings.pairs = ["BTCUSDT"]
        test_liquidation_settings.exchange = "okx"  # Different exchange
        await db_session.commit()
        
        mock_bot = MagicMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        liquidation_info = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "price": "50000",
            "quantity": "0.1",
        }
        
        with patch(
            "bot.services.liquidation_monitor.liquidation_starter.get_active_liq_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = [test_liquidation_settings]
            
            await process_liquidation(mock_bot, "Binance", liquidation_info)
            
            # Should not send message (wrong exchange)
            mock_bot.send_message.assert_not_called()

    async def test_process_liquidation_long_vs_short(
        self, db_session: AsyncSession, test_liquidation_settings
    ):
        """Test liquidation type detection (long vs short)."""
        test_liquidation_settings.enabled = True
        test_liquidation_settings.threshold = 1000.0
        test_liquidation_settings.pairs = ["BTCUSDT"]
        test_liquidation_settings.exchange = "binance"
        await db_session.commit()
        
        mock_bot = MagicMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        # Test SELL (long liquidation)
        liquidation_info = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "price": "50000",
            "quantity": "0.1",
        }
        
        with patch(
            "bot.services.liquidation_monitor.liquidation_starter.get_active_liq_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = [test_liquidation_settings]
            
            await process_liquidation(mock_bot, "Binance", liquidation_info)
            
            mock_bot.send_message.assert_called_once()
            message_text = mock_bot.send_message.call_args[0][1]
            assert "Long liquidation" in message_text or "📉" in message_text

