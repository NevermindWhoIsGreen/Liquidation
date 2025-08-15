import asyncio
import logging
import websockets
import json

from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Message, LinkPreviewOptions
from aiogram.filters import CommandStart, Command
from aiogram.utils.formatting import Bold

from config.base import settings

MIN_USDT = 1000

users: list[dict[str, Any]] = []

logging.basicConfig(level=logging.INFO)

bot: Bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
dp = Dispatcher()


@dp.message(CommandStart())
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


@dp.message(Command)
async def cmd_help(message: Message):
    if not message.from_user:
        await message.answer("❗️ Error: User data not found.")
        return

    help_text = (
        f"{Bold('Help')}\n\n"
        f"TODO: help here\n"
    )

    await message.answer(help_text)


async def process_liquidation(order: dict[str, Any]):
    symbol: str = order["o"]["s"]
    side = order["o"]["S"]  # BUY / SELL
    price = float(order["o"]["ap"])
    quantity = float(order["o"]["q"])
    usd_value = price * quantity
    # if usd_value >= MIN_USDT and symbol.endswith("USDT") and symbol not in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    if usd_value >= MIN_USDT and symbol in ["BTCUSDT"]:
        explanation = "❓ Неизвестный тип ликвидации"
        if side == "BUY":
            explanation = "🚀 Ликвидация Шорта (рынок рос)"
        elif side == "SELL":
            explanation = "📉 Ликвидация Лонга (рынок падал)"
        text = (
            f"💥 Ликвидация!\n"
            f"📌 {symbol} | {explanation}\n"
            f"💰 Объём: {usd_value:,.0f} USDT\n"
            f"💵 Цена: {price}\n"
            f"🔗 Линк: https://www.binance.com/uk-UA/futures/{symbol}\n"
        )
        options_1 = LinkPreviewOptions(is_disabled=True)
        for user in users:
            try:
                # if TRASH_COINS_ONLY and price < 1:
                await bot.send_message(user["id"], text, link_preview_options=options_1)
            except Exception as e:
                print(f"Ошибка при отправке сообщения подписчику {user}: {e}")


async def command_start_handler() -> None:
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    async with websockets.connect(url) as ws:
        print("✅ Подключено к Binance WS")
        async for msg in ws:
            order: dict[str, Any] = json.loads(msg)
            await process_liquidation(order)


async def main(bot: Bot) -> None:
    asyncio.create_task(command_start_handler())
    await dp.start_polling(bot) # type: ignore


if __name__ == "__main__":
    asyncio.run(main(bot))
