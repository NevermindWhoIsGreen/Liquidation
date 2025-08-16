from aiogram import Bot
import websockets
import json

from typing import Any

from aiogram.types import LinkPreviewOptions

from bot.handlers.base import users


MIN_USDT = 1000


async def process_liquidation(bot: Bot, order: dict[str, Any]):
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


async def start_handler(bot: Bot) -> None:
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    async with websockets.connect(url) as ws:
        print("✅ Подключено к Binance WS")
        async for msg in ws:
            order: dict[str, Any] = json.loads(msg)
            await process_liquidation(bot, order)
