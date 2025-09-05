from typing import Protocol, Any

from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import (
    Message,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot import CRUD
from bot.filters.user_filters import UserFilter
from bot.models.user import UserDB
from bot.schemas.liquidation_settings import LiquidationSettingsCreate, LiquidationSettingsUpdate


router = Router()
router.message.filter(UserFilter())
router.callback_query.filter(UserFilter())


class TypeLMSCallback(Protocol):
    data: str = ""
    message: Message

    async def answer(self, *args: Any, **kwargs: Any) -> None: ...


class MonitorSettings(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_threshold = State()
    waiting_for_pairs = State()
    waiting_for_custom_threshold = State()
    waiting_for_custom_pairs = State()


def exchange_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Binance", callback_data="exchange:binance")],
            [InlineKeyboardButton(text="OKX", callback_data="exchange:okx")],
            [InlineKeyboardButton(text="BitMEX", callback_data="exchange:bitmex")],
        ]
    )


def threshold_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1000", callback_data="threshold:1000"),
                InlineKeyboardButton(text="5000", callback_data="threshold:5000"),
            ],
            [
                InlineKeyboardButton(text="50000", callback_data="threshold:50000"),
                InlineKeyboardButton(
                    text="Ввести своё", callback_data="threshold:custom"
                ),
            ],
        ]
    )


def pairs_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="BTCUSDT", callback_data="pair:BTCUSDT"),
                InlineKeyboardButton(text="ETHUSDT", callback_data="pair:ETHUSDT"),
            ],
            [
                InlineKeyboardButton(text="TIAUSDT", callback_data="pair:TIAUSDT"),
                InlineKeyboardButton(
                    text="Ввести вручную", callback_data="pairs:custom"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Завершить выбор", callback_data="pairs:done"
                )
            ],
        ]
    )


# --- Handlers ---
@router.message(F.text == "/setup_lm")
async def cmd_set_monitor(message: Message, state: FSMContext):
    await message.answer("Select exchange:", reply_markup=exchange_kb())
    await state.set_state(MonitorSettings.waiting_for_exchange)


@router.callback_query(
    MonitorSettings.waiting_for_exchange, F.data.startswith("exchange:")
)
async def process_exchange(callback: TypeLMSCallback, state: FSMContext):
    _, exchange = callback.data.split(":")
    await state.update_data(exchange=exchange)
    await callback.message.edit_text(
        "Select minimum liquidation price:", reply_markup=threshold_kb()
    )
    await state.set_state(MonitorSettings.waiting_for_threshold)


@router.callback_query(
    MonitorSettings.waiting_for_threshold, F.data.startswith("threshold:")
)
async def process_threshold(callback: TypeLMSCallback, state: FSMContext):
    _, value = callback.data.split(":")
    if value == "custom":
        await callback.message.answer("Enter the minimum liquidation price manually:")
        await state.set_state(MonitorSettings.waiting_for_custom_threshold)
        return

    await state.update_data(threshold=float(value))
    await callback.message.edit_text("Select pairs:", reply_markup=pairs_kb())
    await state.set_state(MonitorSettings.waiting_for_pairs)


@router.message(MonitorSettings.waiting_for_custom_threshold)
async def process_custom_threshold(message: Message, state: FSMContext):
    try:
        threshold = float(message.text or 0)
    except ValueError:
        await message.answer("Please enter a number:")
        return

    await state.update_data(threshold=threshold)
    await message.answer("Select pairs:", reply_markup=pairs_kb())
    await state.set_state(MonitorSettings.waiting_for_pairs)


@router.callback_query(MonitorSettings.waiting_for_pairs, F.data.startswith("pair:"))
async def process_pair(callback: TypeLMSCallback, state: FSMContext):
    _, pair = callback.data.split(":")
    data = await state.get_data()
    pairs = data.get("pairs", [])
    if pair not in pairs:
        pairs.append(pair)
    await state.update_data(pairs=pairs)
    await callback.answer(f"Added: {pair}")


@router.callback_query(MonitorSettings.waiting_for_pairs, F.data == "pairs:custom")
async def process_custom_pairs(callback: TypeLMSCallback, state: FSMContext):
    await callback.message.answer(
        "Enter the list of pairs separated by commas (e.g.: BTCUSDT, ETHUSDT):"
    )
    await state.set_state(MonitorSettings.waiting_for_custom_pairs)


@router.message(MonitorSettings.waiting_for_custom_pairs)
async def process_custom_pairs_input(message: Message, state: FSMContext):
    raw_pairs = (message.text or "").replace(" ", "")
    pairs = [p.upper() for p in raw_pairs.split(",") if p]
    await state.update_data(pairs=pairs)
    await message.answer(
        "✅ Pairs saved! If you want to add more, use the buttons below.",
        reply_markup=pairs_kb(),
    )
    await state.set_state(MonitorSettings.waiting_for_pairs)


@router.callback_query(MonitorSettings.waiting_for_pairs, F.data == "pairs:done")
async def process_done(
    callback: TypeLMSCallback, state: FSMContext, db: AsyncSession, user: User
):
    data = await state.get_data()
    settings = await CRUD.liquidation_settings.get_by_user_id(db, user_id=user.id)
    if not settings:
        data.update(user_id=user.id, enabled=True)
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

    await callback.message.edit_text(
        f"✅ Liquidation monitor settings updated!\n\n"
        f"Exchange: {settings.exchange}\n"
        f"Threshold: {settings.threshold}\n"
        f"Pairs: {', '.join(settings.pairs)}"
    )
    await state.clear()


@router.message(Command("start_lm"))
async def cmd_start_liquidation_monitor(message: Message, db: AsyncSession, user: User):
    await CRUD.liquidation_settings.toggle_monitor(db, user_id=user.id, turn_on=True)
    await message.answer("Start liquidation monitor")


@router.message(Command("stop_lm"))
async def cmd_stop_liquidation_monitor(message: Message, db: AsyncSession, user: User):
    await CRUD.liquidation_settings.toggle_monitor(db, user_id=user.id, turn_on=False)
    await message.answer("Stop liquidation monitor")


@router.message(Command("set_threshold"))
async def cmd_set_threshold(message: Message, db: AsyncSession, user_db: UserDB):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer(
            "❗ Enter the threshold after the command. Example: /set_threshold 30000"
        )

    try:
        new_threshold = float(parts[1])
    except ValueError:
        return await message.answer("❗ Invalid format. A number is required.")

    await db.refresh(user_db, ("liquid_monitor_settings",))
    settings = user_db.liquid_monitor_settings
    if not settings:
        return await message.answer("No settings pls type /setup_lm")

    settings.threshold = new_threshold
    await db.commit()
    await message.answer(f"✅ Liquidation threshold updated: {new_threshold}")


@router.message(Command("set_pairs"))
async def cmd_set_pairs(message: Message, db: AsyncSession, user_db: UserDB):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer(
            "❗ Specify pairs separated by spaces. Example: /set_pairs BTCUSDT, ETHUSDT"
        )

    pairs = parts[1].upper().replace(" ", "").split(",")
    await db.refresh(user_db, ("liquid_monitor_settings",))
    settings = user_db.liquid_monitor_settings
    if not settings:
        return await message.answer("No settings pls type /setup_lm")

    settings.pairs = pairs
    await db.commit()
    return await message.answer(f"✅ Pairs list updated: {', '.join(pairs)}")


@router.message(Command("show_lm_settings"))
async def cmd_show_liquidation_monitor_settings(message: Message, db: AsyncSession, user_db: UserDB):
    await db.refresh(user_db, ("liquid_monitor_settings",))
    settings = user_db.liquid_monitor_settings
    if not settings:
        return await message.answer("No settings pls type /setup_lm")

    return await message.answer(
        f"✅ Liquidation monitor settings:\n\n"
        f"Exchange: {settings.exchange}\n"
        f"Threshold: {settings.threshold}\n"
        f"Pairs: {', '.join(settings.pairs)}\n"
        f"Status: {'active' if settings.enabled else 'not active'}"
    )


@router.message(Command("drop_lm_settings"))
async def cmd_drop_liquidation_monitor_settigngs(message: Message, db: AsyncSession, user_db: UserDB):
    await db.refresh(user_db, ("liquid_monitor_settings",))
    if user_db.liquid_monitor_settings:
        await CRUD.liquidation_settings.delete(
            db, id=user_db.liquid_monitor_settings.id
        )
        return await message.answer("Liquidation settings deleted")
    return await message.answer("No settings pls type /setup_lm")
