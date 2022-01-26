# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Bot import Bot
    from .ProtocolWare import ProtocolWare

import typing
from .Message import MessageContent, RepliedMessage, ReceivedMessage
from .Contact import Friend, Stranger, GroupAnonymousMember, GroupMember, Group


class BotWare:
    """
    Serve as a plain flat interface for bot protocol, to update this framework in a simple fashion
    """
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
        msg: ReceivedMessage = ReceivedMessage()
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._reply = reply
        if is_friend:
            msg._channel = Friend(sender_id)
            msg._sender = Friend(sender_id)
        else:
            msg._channel = Stranger(sender_id, from_channel)
            msg._sender = Stranger(sender_id, from_channel)

        if self._bot._on_private_msg is not None:
            await self._bot._on_private_msg(msg)

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
        msg: ReceivedMessage = ReceivedMessage()
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._reply = reply
        if is_anonymous:
            msg._channel = Group(group_id)
            msg._sender = GroupAnonymousMember(sender_id, group_id)
        else:
            msg._channel = Group(group_id)
            msg._sender = GroupMember(sender_id, group_id)

        if self._bot._on_group_msg is not None:
            await self._bot._on_group_msg(msg)

    async def remove_friend_from_contact(self, id: int):
        """
        Remove a friend from bot's contact storage

        :param id: user id
        """
        if self._bot.contact._friends is None:
            return None
        if id in self._bot.contact._friends:
            del self._bot.contact._friends[id]

    async def add_friend_to_contact(self, id: int):
        """
        Add a friend to bot's contact storage

        :param id: user id
        """
        # ignore those event if contact is not used
        if self._bot.contact._friends is None:
            return
        self._bot.contact._friends[id] = Friend(id)

    async def remove_group_from_contact(self, id: int):
        """
        Remove a group from bot's contact storage

        :param id: group id
        """
        if self._bot.contact._groups is None:
            return None
        if id in self._bot.contact._groups:
            del self._bot.contact._groups[id]

    async def add_group_to_contact(self, id: int):
        """
        Add a group to bot's contact storage

        :param id: group id
        """
        # ignore those event if contact is not used
        if self._bot.contact._groups is None:
            return
        self._bot.contact._groups[id] = Group(id)
