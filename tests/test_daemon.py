#!/usr/bin/env python
import asyncio

from context import pyasyncbot

from pyasyncbot import Bot, BotConfig
from pyasyncbot.Message import ReceivedMessage
import signal

bot = Bot(BotConfig(
    bot_protocol='MyBotProtocol',
    http_setting=BotConfig.HTTPClientSetting('127.0.0.1', 8888),
    ws_setting=BotConfig.WebSocketClientSetting('127.0.0.1', 8888)
))


# setup exit notification
def signal_handler(sig, frame):
    print('Request stopping...')
    bot.request_stop()


signal.signal(signal.SIGINT, signal_handler)


@bot.on_private_message
async def on_private_message(msg: ReceivedMessage):
    print(msg)
    replied = await msg.reply(msg.get_content())
    await asyncio.sleep(5)
    await replied.revoke()


@bot.on_group_message
async def on_group_message(msg: ReceivedMessage):
    print(msg)
    if msg.get_channel().get_id() == 934358995:
        replied = await msg.reply(msg.get_content())
        await asyncio.sleep(5)
        await replied.revoke()


@bot.on_private_revoke
async def on_private_revoke(msg):
    print(msg)


@bot.on_group_revoke
async def on_group_revoke(msg):
    print(msg)
    await asyncio.sleep(5)


exit(bot.run_as_daemon())
