from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove, User
from aiogram.filters import CommandStart, Command
from aiogram.utils.formatting import Bold, as_marked_section

from bot import CRUD
from bot.filters.user_filters import UserFilter
from bot.schemas.user import UserCreate


router = Router()
router.message.filter(UserFilter())


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession, user: User):
    s_user = UserCreate.model_validate(user, from_attributes=True)
    user_db = await CRUD.user.get(db, id=s_user.id)
    if not user_db:
        user_db = await CRUD.user.create(db, obj_in=s_user)

    await message.answer(
        f"Hello, {user.full_name}!\n"
        f"Your ID: {user_db.id}\n"
        f"This bot is created to monitor user liquidations on exchanges (Binance).\n"
        f"For more detailed information, please use the /help command.",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, user: User):
    help_text = as_marked_section(
        Bold("Help"),
        "Available commands:",
        " /start - start the bot",
        " /stop - stop the bot and clean up all data",
        " /setup_lm - start setting up liquidation monitor settings",
        " /start_lm & /stop_lm - start/stop the liquidation monitor",
        " /set_threshold - set the minimum liquidation amount",
        " /set_pairs - set trading pairs",
        " /show_lm_settings - check liquidation monitor settings",
        " /drop_lm_settings - delete liquidation monitor settings",
        marker="• ",
    )

    await message.answer(**help_text.as_kwargs())


@router.message(Command("stop"))
async def cmd_stop(message: Message, db: AsyncSession, user: User):
    answer = "Goodbye\n"
    if user_db := await CRUD.user.delete(db, id=user.id):
        answer = f"Goodbye, {user_db.username}!\n"
    await message.answer(
        f"{answer} You have been unsubscribed from notifications.",
        reply_markup=ReplyKeyboardRemove(),
    )
