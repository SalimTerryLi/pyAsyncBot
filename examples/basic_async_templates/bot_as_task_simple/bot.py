#!/usr/bin/env python

import asyncio

from pyasyncbot import Bot, BotConfig
from pyasyncbot.Message import ReceivedPrivateMessage, ReceivedGroupMessage, RevokedMessage
from pyasyncbot.Event import BotEvent


bot = Bot(BotConfig(
    bot_protocol='MyBotProtocol',
    http_setting=BotConfig.HTTPClientSetting('127.0.0.1', 8888),
    ws_setting=BotConfig.WebSocketClientSetting('127.0.0.1', 8888)
))


@bot.on_private_message
async def on_private_message(msg: ReceivedPrivateMessage):
    print(msg)


@bot.on_group_message
async def on_group_message(msg: ReceivedGroupMessage):
    print(msg)


@bot.on_private_revoke
async def on_private_revoke(msg: RevokedMessage):
    print(msg)


@bot.on_group_revoke
async def on_group_revoke(msg: RevokedMessage):
    print(msg)


@bot.on_event
async def on_event(event: BotEvent):
    print(event)


@bot.on_framework_ready
async def bot_ready():
    pass


async def foo():
    # start bot here as a separate task
    bot_task = asyncio.create_task(bot.run_as_task())
    # stop the bot after 5s
    await asyncio.sleep(5)
    bot.request_stop()
    # make sure bot exited
    return await bot_task


asyncio.run(foo())
