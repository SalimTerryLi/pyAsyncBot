# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Bot import Bot
    from .ProtocolWare import ProtocolWare

import typing
from .Message import MessageContent, RepliedMessage


class BotWare:
    _bot: Bot
    _protoware: ProtocolWare

    def __init__(self, bot: Bot, protoware: ProtocolWare):
        self._bot = bot
        self._protoware = protoware

    async def deliver_private_msg(self, time: datetime.datetime, sender_id: int, msgid: str, msgcontent: MessageContent,
                                  is_friend: bool = True, from_channel: int = None,
                                  reply: RepliedMessage = None):
        """
        Call this func to deliver a private message event to bot payload

        :param time: time of message
        :param sender_id: user id
        :param msgid: msg id
        :param msgcontent: parsed msg content object
        :param is_friend: friend, or stranger
        :param from_channel: If it is from a stranger then this field is a must
        :param reply: parsed reply info object
        """
        pass

    async def deliver_group_msg(self, time: datetime.datetime, sender_id: int, group_id: int, msgid: str, msgcontent: MessageContent,
                                is_anonymous: bool = False,
                                reply: RepliedMessage = None):
        """
        Call this func to deliver a group message event to bot payload

        :param time: time of message
        :param sender_id: user id
        :param group_id: group id
        :param msgid: msg id
        :param msgcontent: parsed msg content object
        :param is_anonymous: is sender anonymous
        :param reply: parsed reply info object
        """
        pass
