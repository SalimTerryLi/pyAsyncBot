#!/usr/bin/env python

from context import oicq_web

import asyncio

from oicq_web import Bot, BotConfig

event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)

bot = Bot(BotConfig(
    bot_protocol='MyBotProtocol',
    http_setting=BotConfig.HTTPClientSetting('127.0.0.1', 8888),
    ws_setting=BotConfig.WebSocketClientSetting('127.0.0.1', 8888)
))


@bot.on_private_message
async def on_private_message(msg):
    print(msg)


@bot.on_group_message
async def on_group_message(msg):
    print(msg)
    await asyncio.sleep(5)


async def foo():
    # start bot here as a separate task
    bot_task = event_loop.create_task(bot.run_as_task())
    # stop the bot after 5s
    await asyncio.sleep(5)
    bot.request_stop()
    # make sure bot exited
    return await bot_task


daemon_task = event_loop.create_task(foo())

event_loop.run_until_complete(daemon_task)

asyncio.set_event_loop(None)
event_loop.close()
