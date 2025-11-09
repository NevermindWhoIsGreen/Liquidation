"""
Pytest configuration and shared fixtures
"""
import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from bot.db.base import Base


# Test database URL - using in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
    }


@pytest.fixture
def sample_liquidation_settings_data():
    """Sample liquidation settings data for testing."""
    return {
        "user_id": 123456789,
        "enabled": True,
        "threshold": 1000.0,
        "exchange": "binance",
        "pairs": ["BTCUSDT", "ETHUSDT"],
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, sample_user_data):
    """Create a test user in the database."""
    from bot import CRUD
    from bot.schemas.user import UserCreate
    
    user_create = UserCreate(**sample_user_data)
    user = await CRUD.user.create(db_session, obj_in=user_create)
    await db_session.commit()
    return user


@pytest.fixture
async def test_liquidation_settings(
    db_session: AsyncSession, test_user, sample_liquidation_settings_data
):
    """Create test liquidation settings in the database."""
    from bot import CRUD
    from bot.schemas.liquidation_settings import LiquidationSettingsCreate
    
    settings_create = LiquidationSettingsCreate(**sample_liquidation_settings_data)
    settings = await CRUD.liquidation_settings.create(
        db_session, obj_in=settings_create
    )
    await db_session.commit()
    return settings


@pytest.fixture
def mock_message():
    """Create a mock Message object for testing handlers."""
    from unittest.mock import AsyncMock, MagicMock
    from aiogram.types import Message, User, Chat
    
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.full_name = "Test User"
    message.from_user.language_code = "en"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    message.answer = AsyncMock()
    message.text = "/start"
    return message


@pytest.fixture
def mock_callback():
    """Create a mock CallbackQuery object for testing handlers."""
    from unittest.mock import AsyncMock, MagicMock
    from aiogram.types import CallbackQuery, Message
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "exchange:binance"
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    return callback

