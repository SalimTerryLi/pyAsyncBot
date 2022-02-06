# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Bot import Bot

from loguru import logger
import typing
from abc import ABC, abstractmethod
import datetime

from .Message import ReceivedMessage, RepliedMessage, MessageContent, RepliedMessageContent, RevokedMessage, SentMessage, ReceivedPrivateMessage, ReceivedGroupMessage
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

    async def deliver_private_msg(self, time: datetime.datetime, sender_id: int, sender_nick: str,
                                  channel_id: int, channel_nick: str, msgid: str,
                                  msgcontent: MessageContent, summary: str, is_friend: bool = True, from_channel: int = None,
                                  from_channel_name: str = None, reply: RepliedMessageContent = None):
        """
        Call this func to deliver a private message event to bot payload

        :param time: time of message
        :param sender_id: who sent the message
        :param sender_nick: his nickname
        :param channel_id: where the message from
        :param channel_nick: his nick
        :param msgid: msg id
        :param msgcontent: parsed msg content object
        :param summary: summary of message, used to generate reply
        :param is_friend: friend, or stranger
        :param from_channel: If it is from a stranger then this field is the group that the one is from
        :param from_channel_name: as above, the group name
        :param reply: parsed reply info object
        """
        msg: ReceivedMessage = ReceivedPrivateMessage(self.__bot.get_contacts())
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._summary = summary
        msg._reply = RepliedMessage(self.__bot.get_contacts(), reply, msg)
        if is_friend:
            msg._channel = await self.__bot.get_contacts().get_friend(channel_id, channel_nick)
            msg._sender = await self.__bot.get_contacts().get_friend(sender_id, sender_nick)
        else:
            msg._ref_channel = await self.__bot.get_contacts().get_group(from_channel, from_channel_name)
            msg._channel = await (await msg._ref_channel.get_member(channel_id, channel_nick)).open_private_channel()
            msg._sender = await (await msg._ref_channel.get_member(sender_id, sender_nick)).open_private_channel()

        if self.__bot._on_private_msg_cb is not None:
            await self.__bot._on_private_msg_cb(msg)

    async def deliver_group_msg(self, time: datetime.datetime, sender_id: int, sender_nick: str, group_id: int,
                                group_name: str, msgid: str, msgcontent: MessageContent, summary: str,
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
        :param summary: summary of message, used to generate reply
        :param is_anonymous: is sender anonymous
        :param reply: parsed reply info object
        """
        msg: ReceivedMessage = ReceivedGroupMessage(self.__bot._contacts)
        msg._time = time
        msg._msgID = msgid
        msg._msgContent = msgcontent
        msg._summary = summary
        msg._reply = RepliedMessage(self.__bot.get_contacts(), reply, msg)
        if is_anonymous:
            msg._channel = await self.__bot.get_contacts().get_group(group_id, group_name)
            msg._sender = GroupAnonymousMember(self.__bot.get_contacts(), sender_id, '', group_id)  # TODO: temporarily use empty nick
        else:
            msg._channel = await self.__bot.get_contacts().get_group(group_id, group_name)
            msg._sender = await msg._channel.get_member(sender_id, sender_nick)

        if self.__bot._on_group_msg_cb is not None:
            await self.__bot._on_group_msg_cb(msg)

    async def deliver_private_revoke(self, time: datetime.datetime, revoker_id: int, channel: int,
                                     is_friend: bool, msgid: str):
        # TODO: avoid force fetching those lists
        """
        Call this func to deliver a private revoke event to bot payload

        :param time: time of revoking
        :param revoker_id: the one who performs revoking
        :param revokee_id: the one whose message was revoked
        :param channel: where the event happened
        :param is_friend: is friend
        :param msgid: the message being revoked
        """
        msg: RevokedMessage = RevokedMessage()
        msg._time = time
        msg._msgid = msgid
        if is_friend:
            msg._channel = await self.__bot.get_contacts().get_friend(channel)
            msg._revoker = msg._channel
        else:
            msg._channel = await self.__bot.get_contacts().get_group(channel)
            msg._revoker = await (await msg._channel.get_member(revoker_id)).open_private_channel()

        if self.__bot._on_private_revoke_cb is not None:
            await self.__bot._on_private_revoke_cb(msg)

    async def deliver_group_revoke(self, time: datetime.datetime, revoker_id: int, group: int,
                                     is_anonymous: bool, msgid: str):
        # TODO: avoid force fetching those lists
        """
        Call this func to deliver a group revoke event to bot payload

        :param time: time of revoking
        :param revoker_id: the one who performs revoking
        :param group: which group
        :param is_anonymous: revoker is anonymous
        :param msgid: message being revoked
        :return:
        """
        msg: RevokedMessage = RevokedMessage()
        msg._time = time
        msg._msgid = msgid
        if is_anonymous:
            msg._channel = await self.__bot.get_contacts().get_group(group)
            msg._revoker = GroupAnonymousMember(self.__bot.get_contacts(), revoker_id, '', group)
        else:
            msg._channel = await self.__bot.get_contacts().get_group(group)
            msg._revoker = await msg._channel.get_member(revoker_id)

        if self.__bot._on_group_revoke_cb is not None:
            await self.__bot._on_group_revoke_cb(msg)

    async def remove_friend_from_contact(self, id: int):
        """
        Remove a friend from bot's contact storage

        :param id: user id
        """
        if self.__bot.get_contacts()._friends is None:
            if id in self.__bot.get_contacts()._friends_tmp:
                del self.__bot.get_contacts()._friends_tmp[id]
            return
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
            if id in self.__bot.get_contacts()._groups_tmp:
                del self.__bot.get_contacts()._groups_tmp[id]
            return
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
        if self.__bot.get_contacts()._groups is None:
            if gid in self.__bot.get_contacts()._groups_tmp:
                del self.__bot.get_contacts()._groups_tmp[uid]
            return
        if gid not in self.__bot.get_contacts()._groups:
            # it is already loaded list
            logger.error('error: group {gid} doesn\' t exist!'.format(gid=gid))
            return
        if self.__bot.get_contacts()._groups[gid]._members is None:
            if uid in self.__bot.get_contacts()._groups[gid]._members_tmp:
                del self.__bot.get_contacts()._groups[gid]._members_tmp[uid]
            return
        del self.__bot.get_contacts()._groups[gid]._members[uid]


class ProtocolWrapper(ABC):
    """
    Defines a set of 'flat' APIs that bot protocol must implement and provide, so that bot framework can make requests.
    """

    @abstractmethod
    async def serv_private_message(self, id: int, msg_content: MessageContent, *, from_channel: int = None, reply: RepliedMessageContent = None) -> str:
        """
        Override this function to implement private message sending

        :param id: user id
        :param msg_content: msg content obj
        :param from_channel: optional reference channel id
        :param reply: reply context
        :return: msgID or None if failed
        """
        pass

    @abstractmethod
    async def serv_group_message(self, id: int, msg_content: MessageContent, *, as_anonymous: bool = False, reply: RepliedMessageContent = None) -> str:
        """
        Override this function to implement group message sending

        :param id: group id
        :param msg_content: msg content obj
        :param as_anonymous: send as anonymous
        :param reply: reply context
        :return: msgID or None if failed
        """
        pass

    @abstractmethod
    async def serv_private_revoke(self, id: int, msgid: str) -> bool:
        """
        Override this function to implement private message revoking

        :param id: user id
        :param msgid: message id
        :return: True if success
        """
        pass

    @abstractmethod
    async def serv_group_revoke(self, id: int, msgid: str) -> bool:
        """
        Override this function to implement group message revoking

        :param id: group id
        :param msgid: message id
        :return: True if success
        """
        pass

    @abstractmethod
    async def query_packed_msg(self, id: str) -> typing.List[GroupedSegment.ContextFreeMessage]:
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
