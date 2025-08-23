from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import Message, User
from aiogram.filters import Command

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from bot import CRUD
from bot.filters.user_filters import UserFilter
from bot.models.liquid_monitor_settings import LiquidMonitorSettingsDB
from bot.models.user import UserDB
from bot.schemas.liquidation_settings import LiquidationSettingsCreate, LiquidationSettingsUpdate


router = Router()
router.message.filter(UserFilter())


# --- FSM States ---
class MonitorSettings(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_threshold = State()
    waiting_for_pairs = State()


@router.message(F.text == "/set_liquid_monitor")
async def cmd_set_monitor(message: Message, state: FSMContext):
    await message.answer("Set exchenge (available now: ['binance']):")
    await state.set_state(MonitorSettings.waiting_for_exchange)


@router.message(MonitorSettings.waiting_for_exchange)
async def process_exchange(message: Message, state: FSMContext):
    exchange = message.text.lower()
    if exchange != "binance":
        await message.answer(
            "Currently, only 'binance' is supported. Please try again:"
        )
        return

    await state.update_data(exchange=exchange)
    await message.answer("Set minimal price of liquidations (threshold):")
    await state.set_state(MonitorSettings.waiting_for_threshold)


@router.message(MonitorSettings.waiting_for_threshold)
async def process_threshold(message: Message, state: FSMContext):
    try:
        threshold = float(message.text)
    except ValueError:
        await message.answer("Invalid value. Please enter a number:")
        return

    await state.update_data(threshold=threshold)
    await message.answer(
        "Enter a list of pairs separated by commas (e.g.: BTCUSDT, ETHUSDT, TIAUSDT):"
    )
    await state.set_state(MonitorSettings.waiting_for_pairs)


@router.message(MonitorSettings.waiting_for_pairs)
async def process_pairs(
    message: Message, state: FSMContext, db: AsyncSession, user: User
):
    raw_pairs = message.text.replace(" ", "")
    pairs = [p.upper() for p in raw_pairs.split(",") if p]

    data = await state.get_data()
    data.update(
        pairs=pairs,
        enabled=True
    )
    settings = await CRUD.liquidation_settings.get_by_user_id(db, user_id=user.id)

    if not settings:
        data.update(user_id=user.id)
        settings = await CRUD.liquidation_settings.create(
            db=db,
            obj_in=LiquidationSettingsCreate.model_validate(data),
        )
    else:
        settings = await CRUD.liquidation_settings.update(
            db=db,
            db_obj=settings,
            obj_in=LiquidationSettingsUpdate.model_validate(data),
        )

    await db.commit()

    await message.answer(
        f"✅ Liquidation monitor settings updated!\n\n"
        f"Exchange: {settings.exchange}\n"
        f"Threshold: {settings.threshold}\n"
        f"Pairs: {', '.join(settings.pairs)}"
    )

    await state.clear()


@router.message(Command("start_liquidation_monitor"))
async def cmd_start_liquidation_monitor(message: Message, db: AsyncSession, user: User):
    await CRUD.liquidation_settings.toggle_monitor(db, user_id=user.id, turn_on=True)
    await message.answer("Start liquidation monitor")


@router.message(Command("stop_liquidation_monitor"))
async def cmd_stop_liquidation_monitor(message: Message, db: AsyncSession, user: User):
    await CRUD.liquidation_settings.toggle_monitor(db, user_id=user.id, turn_on=False)
    await message.answer("Stop liquidation monitor")