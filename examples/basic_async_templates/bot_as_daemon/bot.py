#!/usr/bin/env python
import asyncio

from pyasyncbot import Bot, BotConfig
from pyasyncbot.Message import ReceivedPrivateMessage, ReceivedGroupMessage, RevokedMessage
from pyasyncbot.Event import BotEvent
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


# attach signal handler for keyboard CTRL+C
signal.signal(signal.SIGINT, signal_handler)


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


# block and run the bot as daemon
exit(bot.run_as_daemon())
