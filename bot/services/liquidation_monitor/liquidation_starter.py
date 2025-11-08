import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
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


async def process_liquidation(bot: Bot, source: str, info: dict[str, Any]):
    symbol = info["symbol"]
    price = float(info["price"])
    quantity = float(info["quantity"])
    usd_value = price * quantity

    settings = await get_active_liq_settings()
    user_ids = [
        s.user_id for s in settings if usd_value >= s.threshold and symbol in s.pairs and source.lower() == s.exchange.lower()
    ]

    if not user_ids:
        return

    explanation = "❓ Unknown liquidation type"
    if info.get("side") == "BUY":
        explanation = "🚀 Short liquidation (market went up)"
    elif info.get("side") == "SELL":
        explanation = "📉 Long liquidation (market went down)"

    text = (
        f"💥 Liquidation [{source}]\n"
        f"📌 {symbol} | {explanation}\n"
        f"💰 Amount: {usd_value:,.0f} USDT\n"
        f"💵 Price: {price}\n"
        f"{info.get('link', '')}"
    )
    options_1 = LinkPreviewOptions(is_disabled=True)
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text, link_preview_options=options_1)
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")


# ----------------------
# Binance Listener
async def binance_listener(bot: Bot):
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    async with websockets.connect(url) as ws:
        print("Connected to Binance")
        async for msg in ws:
            data = json.loads(msg)
            await process_liquidation(
                bot,
                "Binance",
                {
                    "symbol": data["o"]["s"],
                    "side": data["o"]["S"],
                    "price": data["o"]["ap"],
                    "quantity": data["o"]["q"],
                    "link": f"https://www.binance.com/uk-UA/futures/{data['o']['s']}",
                },
            )


# ----------------------
# BitMEX Listener
async def bitmex_listener(bot: Bot):
    url = "wss://www.bitmex.com/realtime?subscribe=liquidation"
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                print("Connected to BitMEX")
                async for msg in ws:
                    data = json.loads(msg)
                    if "data" in data:
                        for order in data["data"]:
                            await process_liquidation(
                                bot,
                                "BitMEX",
                                {
                                    "symbol": order["symbol"],
                                    "side": order["side"],
                                    "price": order["price"],
                                    "quantity": order.get("leavesQty", 0),
                                },
                            )
        except ConnectionClosedError as e:
            print(f"BitMEX WS closed: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"BitMEX error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)


# ----------------------
# OKX Listener
async def okx_listener(bot: Bot):
    url = "wss://ws.okx.com:8443/ws/v5/public"
    async with websockets.connect(url) as ws:
        print("Connected to OKX")
        await ws.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "args": [
                        {
                            "channel": "liquidation-orders",
                            "instType": "FUTURES",
                        }
                    ],
                }
            )
        )
        async for msg in ws:
            data = json.loads(msg)
            for entry in data.get("data", []):
                await process_liquidation(
                    bot,
                    "OKX",
                    {
                        "symbol": entry["instId"],
                        "side": entry["side"],
                        "price": entry["p"],
                        "quantity": entry["sz"],
                    },
                )


async def start_handler(bot: Bot):
    await asyncio.gather(
        binance_listener(bot),
        bitmex_listener(bot),
        okx_listener(bot),
    )
