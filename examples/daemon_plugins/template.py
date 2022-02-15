# -*- coding: utf-8 -*-

"""
插件模板
"""

from pyasyncbot import Bot
from pyasyncbot.Event import BotEvent
from pyasyncbot.Message import ReceivedPrivateMessage, ReceivedGroupMessage, RevokedMessage


async def on_loaded(bot: Bot):
    # get called when bot framework is up and running
    pass


async def on_private_message(msg: ReceivedPrivateMessage):
    print(msg)


async def on_group_message(msg: ReceivedGroupMessage):
    print(msg)


async def on_private_revoke(msg: RevokedMessage):
    print(msg)


async def on_group_revoke(msg: RevokedMessage):
    print(msg)


async def on_event(event: BotEvent):
    print(event)
