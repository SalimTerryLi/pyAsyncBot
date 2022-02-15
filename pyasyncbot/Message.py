# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Contacts import *

import datetime
from typing import Union
import ast
import dataclasses

from .MsgContent import *


@dataclasses.dataclass
class PrivateMessageContext:
    # TODO: Proper docstring
    """Private Message context that Bot Protocol must provide to the framework

    Args:
        time: time of message
        sender_id: who sent the message
        sender_nick: his nickname
        channel_id: where the message from
        channel_nick: his nick
        msgid: msg id
        msgcontent: parsed msg content object
        summary: summary of message, used to generate reply
        is_friend: friend, or stranger
        from_channel: If it is from a stranger then this field is the group that the one is from
        from_channel_name: as above, the group name
        reply: parsed reply info object
    """
    time: datetime.datetime
    sender_id: int
    sender_nick: str
    channel_id: int
    channel_nick: str
    msgid: str
    msgcontent: MessageContent
    summary: str
    is_friend: bool = True
    from_channel: int = None,
    from_channel_name: str = None
    reply: RepliedMessageContent = None


@dataclasses.dataclass
class GroupMessageContext:
    """Group Message context that Bot Protocol must provide to the framework

    Args:
        time: time of message
        sender_id: user id
        sender_nick: user nickname in the channel
        group_id: group id
        group_name: group name
        msgid: msg id
        msgcontent: parsed msg content object
        summary: summary of message, used to generate reply
        is_anonymous: is sender anonymous
        reply: parsed reply info object
    """
    time: datetime.datetime
    sender_id: int
    sender_nick: str
    group_id: int
    group_name: str
    msgid: str
    msgcontent: MessageContent
    summary: str
    is_anonymous: bool = False
    reply: RepliedMessageContent = None


class RepliedMessage:
    """
    A small structure which contains information of a replied reference message.
    """

    def __init__(self, content: RepliedMessageContent, ctx: ReceivedMessage):
        self._content = content
        self._ctx = ctx

    def __str__(self):
        if self._content is None:
            return str(None)
        return str(self._content)

    def get_msgid(self):
        """
        Advanced: Get the message id of the message being replied

        :return: msgid
        """
        return self._content.to_msgid

    async def get_original_msg(self) -> Union[ReceivedMessage, None]:
        """
        Get the original message this one is replied to.

        May fail due to the replied message is flushed out of chat history, or it is a constructed one

        Channel will be updated according to current contacts. May be None if the guy left. Sender may become User object

        :return: content or None
        """
        ctx = await self._ctx._contacts._proto_wrapper.query_msg_by_id(self._ctx._channel.get_type(), self._ctx._channel.get_id(), self._content.to_msgid)
        if isinstance(ctx, PrivateMessageContext):
            msg: ReceivedMessage = ReceivedPrivateMessage(self._ctx._contacts)
            msg._time = ctx.time
            msg._msgID = ctx.msgid
            msg._msgContent = ctx.msgcontent
            msg._summary = ctx.summary
            if ctx.reply is not None:
                msg._reply = RepliedMessage(ctx.reply, msg)
            # things may change and ctx.is_friend is useless now. must re-analyse the contacts

            # try to find the channel in your friend list
            msg._channel = await self._ctx._contacts.get_friend(ctx.channel_id)
            if msg._channel is None:
                # he is not your friend now
                if ctx.from_channel is not None:
                    # he wasn't your friend before, either
                    # so he reached you from a group
                    msg._ref_channel = await self._ctx._contacts.get_group(ctx.from_channel)
                    if msg._ref_channel is None:
                        # but you left that group
                        pass
                    else:
                        # try to get touch with him by the group as group member
                        he_as_group_member =  await msg._ref_channel.get_member(ctx.channel_id, ctx.channel_nick)
                        if he_as_group_member is None:
                            # but he left that group
                            pass
                        else:
                            # he is in the group, a stranger channel is set up
                            msg._channel = await he_as_group_member.open_private_channel()
                else:
                    # he was your friend
                    pass
            # deal with sender
            if await (self._ctx._contacts.get_myself()).get_id() == ctx.sender_id:
                msg._sender = await (self._ctx._contacts.get_myself())
            else:
                msg._sender = await self._ctx._contacts.get_friend(ctx.sender_id)
                if msg._sender is None:
                    msg._sender = User(ctx.sender_id, ctx.sender_nick)
            return msg
        elif isinstance(ctx, GroupMessageContext):
            msg: ReceivedMessage = ReceivedGroupMessage(self._ctx._contacts)
            msg._time = ctx.time
            msg._msgID = ctx.msgid
            msg._msgContent = ctx.msgcontent
            msg._summary = ctx.summary
            if ctx.reply is not None:
                msg._reply = RepliedMessage(ctx.reply, msg)
            if ctx.is_anonymous:
                msg._channel = await self._ctx._contacts.get_group(ctx.group_id)
                if msg._channel is None:
                    # Seems you've left the group
                    msg._sender = User(ctx.sender_id, ctx.sender_nick)
                else:
                    msg._sender = GroupAnonymousMember(self._ctx._contacts, ctx.sender_id, '',
                                                   ctx.group_id)  # TODO: temporarily use empty nick
            else:
                msg._channel = await self._ctx._contacts.get_group(ctx.group_id, ctx.group_name)
                if msg._channel is None:
                    # Seems you've left the group
                    msg._sender = User(ctx.sender_id, ctx.sender_nick)
                else:
                    msg._sender = await msg._channel.get_member(ctx.sender_id, ctx.sender_nick)
                    if msg._sender is None:
                        # Seems he had left the group
                        msg._sender = User(ctx.sender_id, ctx.sender_nick)
            return msg

    async def get_sender(self) -> Union[Friend, GroupMember, Stranger, GroupAnonymousMember]:
        """
        Get the sender of the message being replied

        :return: sender
        """
        pass


class ReceivedMessage:
    """
    Received message
    """

    def __init__(self, contacts):
        self._contacts = contacts
        self._time: datetime.datetime = None
        self._channel: Union[Friend, Stranger, Group] = None
        self._sender: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None
        self._msgID: str = None
        self._msgContent: MessageContent = None
        self._reply: RepliedMessage = None
        self._summary: str = None

    def __str__(self):
        return str({
            'time': str(self._time),
            'sender': str(self._sender),
            'channel': str(self._channel),
            'msgID': self._msgID,
            'msgContent': str(self._msgContent),
            'reply_to': str(self._reply),
        })

    def get_content(self) -> MessageContent:
        """
        Get the message content

        :return: a content object
        """
        return self._msgContent

    def get_msg_id(self) -> str:
        """
        Advanced: get message ID

        :return: message id as string
        """
        return self._msgID

    def get_replied(self) -> Union[RepliedMessage, None]:
        """
        Get the replied message obj. None if not exist

        :return: replied message obj
        """
        return self._reply

    async def reply(self, content: MessageContent) -> SentMessage:
        """
        Reply to the channel which this message comes from

        :param content: message content
        :return: sent msg obj or None if failed
        """
        return await self._channel.send_msg(content)

    async def quoted_reply(self, content: MessageContent) -> SentMessage:
        """
        Reply to original message with its content summarized and quoted

        :param content: message content
        :return: msgID of reply msg or None if failed
        """
        reply_content = RepliedMessageContent(
            to_msgid=self._msgID,
            to_uid=self._sender.get_id(),
            text=self._summary,
            time=self._time
        )
        return await self._channel.send_msg(content, reply_content)


class ReceivedPrivateMessage(ReceivedMessage):
    def __init__(self, contacts):
        super().__init__(contacts)
        self._ref_channel: Group = None

    def __str__(self):
        dictionary = ast.literal_eval(super().__str__())
        dictionary['ref_channel'] = str(self._ref_channel)
        return str(dictionary)

    def get_ref_channel(self) -> Union[Group, None]:
        """
        If the message is from a stranger, then the group he started the private channel can be fetched here.

        :return: Group or None
        """
        return self._ref_channel

    def get_channel(self) -> Union[Friend, Stranger]:
        """
        Get the channel this message comes from

        :return: channel obj
        """
        return self._channel

    def get_sender(self) -> Union[Friend, Stranger, User]:
        """
        Get the sender of this message

        :return: sender object
        """
        return self._sender
    

class ReceivedGroupMessage(ReceivedMessage):
    def get_channel(self) -> Union[Group, None]:
        """
        Get the group this message comes from

        :return: channel obj
        """
        return self._channel

    def get_sender(self) -> Union[GroupMember, GroupAnonymousMember, User, None]:
        """
        Get the sender of this message

        :return: sender object
        """
        return self._sender


class SentMessage:
    """
    A message that is sent by us
    """
    _msgid: str
    _channel: Channel

    def __init__(self):
        self._msgid = None
        self._channel = None

    async def revoke(self) -> bool:
        return await self._channel.revoke_msg(self._msgid)


class RevokedMessage:
    """
    Revoked Message
    """

    def __init(self):
        self._time: datetime.datetime = None
        self._msgid: str = None
        self._channel: Channel = None
        self._revoker: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None

    def __str__(self):
        return str({
            'time': str(self._time),
            'channel': str(self._channel),
            'revoker': str(self._revoker),
            'msgid': self._msgid,
        })

    def get_channel(self) -> Channel:
        """
        Get the channel this message comes from

        :return: channel obj
        """
        return self._channel

    def get_revoker(self) -> User:
        """
        Get the one who revoked the message

        :return: user object
        """
        return self._revoker

    async def get_remoked_msg(self) -> ReceivedMessage:
        """
        Get the original message which was revoked

        May fail due to the replied message is flushed out of chat history

        :return: message object, None if failed to get
        """
        pass
