#!/usr/bin/env python

import asyncio

from pyasyncbot import Bot, BotConfig
from pyasyncbot.Message import ReceivedPrivateMessage, ReceivedGroupMessage, RevokedMessage
from pyasyncbot.Event import BotEvent


# manually create and set an event loop for current thread
# asyncio.get_event_loop() will do the same thing
event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)

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


async def foo():
    # start bot here as a separate task
    bot_task = event_loop.create_task(bot.run_as_task())
    # just wait for 5s
    await asyncio.sleep(5)
    # stop the bot
    bot.request_stop()
    # wait until bot task exited
    return await bot_task


# your main async task is here
daemon_task = event_loop.create_task(foo())

# block and run your own event loop
event_loop.run_until_complete(daemon_task)

# cleanup
asyncio.set_event_loop(None)
event_loop.close()
