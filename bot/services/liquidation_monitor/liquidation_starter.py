import websockets
import json

from typing import Any

from aiogram import Bot
from aiogram.types import LinkPreviewOptions

from bot import CRUD
from bot.db.connection import db_session_maker
from bot.models.liquid_monitor_settings import LiquidMonitorSettingsDB


async def get_active_liq_settings() -> list[LiquidMonitorSettingsDB]:
    async with db_session_maker() as db:
        return list(await CRUD.liquidation_settings.get_multi(
            db, where_conditions=[LiquidMonitorSettingsDB.enabled]
        ))


async def process_liquidation(bot: Bot, order: dict[str, Any]):

    symbol: str = order["o"]["s"]
    side = order["o"]["S"]  # BUY / SELL
    price = float(order["o"]["ap"])
    quantity = float(order["o"]["q"])
    usd_value = price * quantity

    # TODO: fix bottleneck
    settings = await get_active_liq_settings()
    user_ids = [setting.user_id for setting in settings if price >= setting.threshold and symbol in setting.pairs]

    explanation = "❓ Unknown liquidation type"
    if side == "BUY":
        explanation = "🚀 Short liquidation (market went up)"
    elif side == "SELL":
        explanation = "📉 Long liquidation (market went down)"
    text = (
        f"💥 Liquidation!\n"
        f"📌 {symbol} | {explanation}\n"
        f"💰 Amount: {usd_value:,.0f} USDT\n"
        f"💵 Price: {price}\n"
        f"🔗 Link: https://www.binance.com/uk-UA/futures/{symbol}\n"
    )
    options_1 = LinkPreviewOptions(is_disabled=True)
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text, link_preview_options=options_1)
        except Exception as e:
            print(f"Error sending message to subscriber {user_id}: {e}")


async def start_handler(bot: Bot) -> None:
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    async with websockets.connect(url) as ws:
        print("✅ Connect to Binance WS")
        async for msg in ws:
            order: dict[str, Any] = json.loads(msg)
            await process_liquidation(bot, order)
