#!/usr/bin/env python

import asyncio

from pyasyncbot import Bot, BotConfig
from pyasyncbot.Message import ReceivedGroupMessage
from pyasyncbot.MsgContent import MessageContent

bot = Bot(BotConfig(
    bot_protocol='MyBotProtocol',
    http_setting=BotConfig.HTTPClientSetting('127.0.0.1', 8888),
    ws_setting=BotConfig.WebSocketClientSetting('127.0.0.1', 8888)
))


@bot.on_group_message
async def on_group_message(msg: ReceivedGroupMessage):
    if '测试' in str(msg.get_content()):
        await msg.reply(
            MessageContent() \
                .add_text('这是一串文本') \
                .add_image(url='https://inews.gtimg.com/newsapp_bt/0/12171811596_909/0') \
                .add_emoji(182).add_mention(msg.get_sender())
        )


asyncio.run(bot.run_as_task())
