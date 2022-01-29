# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Bot import Bot

import typing
from abc import ABC, abstractmethod
import datetime

from .Message import ReceivedMessage, RepliedMessage, MessageContent, RepliedMessageContent
from .MsgContent import GroupedSegment
from .Contacts import Friend, Stranger, GroupMember, GroupAnonymousMember, Group


class BotWrapper:
    """
    Provide a set of methods to let bot protocol instance interacts with bot framework.

    Designed to be flat and and simple
    """
    def __init__(self, bot: Bot):
        self.__bot: Bot = bot

    def create_task(self, coro: typing.Awaitable, name: str):
        """
        Call this to start a new task with given co-routine

        :param name: task name
        :param coro: task coroutine
        """
        return self.__bot._create_bot_task(coro, name)

    async def deliver_private_msg(self, time: datetime.datetime, sender_id: int, sender_nick: str, msgid: str,
                                  msgcontent: MessageContent, is_friend: bool = True, from_channel: int = None,
                                  reply: RepliedMessageContent = None):
        """
        Call this func to deliver a private message event to bot payload

        :param time: time of message
        :param sender_id: user id
        :param sender_nick: user nickname in the channel
        :param msgid: msg id
        :param msgcontent: parsed msg content object
        :param is_friend: friend, or stranger
        :param from_channel: If it is from a stranger then this field is a must
        :param reply: parsed reply info object
        """
        msg: ReceivedMessage = ReceivedMessage(self.__bot.get_contacts())
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._reply = RepliedMessage(self.__bot.get_contacts(), reply, msg)
        if is_friend:
            msg._channel = await self.__bot.get_contacts().get_friend(sender_id)
            msg._sender = msg._channel
        else:
            msg._channel = await self.__bot.get_contacts().get_group(from_channel)
            msg._sender = await msg._channel.get_member(sender_id)

        if self.__bot._on_private_msg_cb is not None:
            await self.__bot._on_private_msg_cb(msg)

    async def deliver_group_msg(self, time: datetime.datetime, sender_id: int, sender_nick: str, group_id: int,
                                group_name: str, msgid: str, msgcontent: MessageContent,
                                is_anonymous: bool = False,
                                reply: RepliedMessageContent = None):
        """
        Call this func to deliver a group message event to bot payload

        :param time: time of message
        :param sender_id: user id
        :param sender_nick: user nickname in the channel
        :param group_id: group id
        :param group_name: group name
        :param msgid: msg id
        :param msgcontent: parsed msg content object
        :param is_anonymous: is sender anonymous
        :param reply: parsed reply info object
        """
        msg: ReceivedMessage = ReceivedMessage(self.__bot._contacts)
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._reply = RepliedMessage(self.__bot.get_contacts(), reply)
        if is_anonymous:
            msg._channel = await self.__bot.get_contacts().get_group(group_id)
            msg._sender = GroupAnonymousMember(self.__bot.get_contacts(), sender_id, '', group_id)  # TODO: temporarily use empty nick
        else:
            msg._channel = await self.__bot.get_contacts().get_group(group_id)
            msg._sender = await msg._channel.get_member(sender_id)

        if self.__bot._on_group_msg_cb is not None:
            await self.__bot._on_group_msg_cb(msg)

    async def remove_friend_from_contact(self, id: int):
        """
        Remove a friend from bot's contact storage

        :param id: user id
        """
        if self.__bot.get_contacts()._friends is None:
            return None
        if id in self.__bot.get_contacts()._friends:
            del self.__bot.get_contacts()._friends[id]

    async def add_friend_to_contact(self, id: int, nick: str):
        """
        Add a friend to bot's contact storage

        :param id: user id
        :param nick: user nickname
        """
        # ignore those event if contact is not used
        if self.__bot.get_contacts()._friends is None:
            return
        self.__bot.get_contacts()._friends[id] = Friend(self.__bot.get_contacts(), id, nick)

    async def remove_group_from_contact(self, id: int):
        """
        Remove a group from bot's contact storage

        :param id: group id
        """
        if self.__bot.get_contacts()._groups is None:
            return None
        if id in self.__bot.get_contacts()._groups:
            del self.__bot.get_contacts()._groups[id]

    async def add_group_to_contact(self, id: int, name: str):
        """
        Add a group to bot's contact storage

        :param id: group id
        :param name: group name
        """
        # ignore those event if contact is not used
        if self.__bot.get_contacts()._groups is None:
            return
        self.__bot.get_contacts()._groups[id] = Group(self.__bot.get_contacts(), id, name)

    async def add_member_to_group_members(self, uid: int, nick: str, gid: int):
        """
        Add a member to the group's member list

        :param uid: which user
        :param nick: user's nickname
        :param gid: which group
        """
        # ignore those event if contact is not used
        if self.__bot.get_contacts()._groups is None:
            return
        if gid not in self.__bot.get_contacts()._groups:
            return
        if self.__bot.get_contacts()._groups[gid]._members is None:
            return
        self.__bot.get_contacts()._groups[gid]._members[uid] = GroupMember(self.__bot.get_contacts(), uid, nick, gid)

    async def remove_member_from_group_members(self, uid: int, gid: int):
        """
        Remove a member from the group's member list

        :param uid: which user
        :param gid: which group
        """
        # ignore those event if contact is not used
        if self.__bot.get_contacts()._groups is None:
            return
        if gid not in self.__bot.get_contacts()._groups:
            return
        if self.__bot.get_contacts()._groups[gid]._members is None:
            return
        del self.__bot.get_contacts()._groups[gid]._members[uid]


class ProtocolWrapper(ABC):
    """
    Defines a set of 'flat' APIs that bot protocol must implement and provide, so that bot framework can make requests.
    """
    @abstractmethod
    async def query_packed_msg(self, id: str) -> GroupedSegment.ContextFreeMessage:
        """
        Override this function to implement content querying of packed message

        :param id: packed msgid
        :return: context-free message obj
        """
        pass

    @abstractmethod
    async def get_friend_list(self) -> typing.Dict[int, str]:
        """
        Override this function to provide friend list content. Normally not need to do cache here.

        :return: {id, nickname} dict
        """
        pass

    @abstractmethod
    async def get_group_list(self) -> typing.Dict[int, str]:
        """
        Override this function to provide group list content. Normally not need to do cache here.

        :return: {id, name} dict
        """
        pass

    @abstractmethod
    async def get_group_members(self, id: int) -> typing.Dict[int, str]:
        """
        Get the group members

        :param id: group id
        :return: {id, nickname} dict
        """
        pass
