import logging

from typing import Any

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.utils.formatting import Bold, as_marked_section

users: list[dict[str, Any]] = [] # TODO: move to db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not message.from_user:
        await message.answer("❗️ Error: User data not found.")
        return

    user_data: dict[str, Any] = {
        "id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "language_code": message.from_user.language_code,
    }

    users.append(user_data)

    logging.info(f"User {user_data['id']} started the bot: {user_data}")

    await message.answer(
        f"Hello, {message.from_user.full_name}!\n"
        f"Your ID: {user_data['id']}\n"
        f"This bot is created to monitor user liquidations on exchanges (Binance).\n"
        f"For more detailed information, please use the /help command.",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    if not message.from_user:
        await message.answer("❗️ Error: User data not found.")
        return

    help_text = as_marked_section(
        Bold("Help"),
        "Available commands:",
        " /start — " + "start the bot",
        " /help — " + "show this help",
        " /settings — " + "configure preferences",
        marker="• ",
    )

    await message.answer(**help_text.as_kwargs())


@router.message(Command("stop"))
async def cmd_stop(message: Message):
    if not message.from_user:
        await message.answer("❗️ Error: User data not found.")
        return

    user_id = message.from_user.id
    global users
    users = [user for user in users if user["id"] != user_id]

    logging.info(f"User {user_id} stopped the bot.")

    await message.answer(
        f"Goodbye, {message.from_user.full_name}!\n"
        f"You have been unsubscribed from notifications.",
        reply_markup=ReplyKeyboardRemove(),
    )
