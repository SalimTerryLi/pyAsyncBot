# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Union
from ujson import dumps

from .MsgContent import *
from .Contact import *


class RepliedMessage:
    """
    A small structure which contains information of a replied reference message.
    """

    def __init__(self):
        self._to: User = None
        self._time: datetime.datetime = None
        self._text: str = None
        self._id: str = None

    def __str__(self):
        return dumps({
            'user_id': str(self._to),
            'time': str(self._time),
            'summary': self._text,
            'msgID': self._id
        }, ensure_ascii=False)

    def get_msgid(self):
        """
        Advanced: Get the message id of the message being replied

        :return: msgid
        """
        return self._id

    async def get_original_msg(self) -> Union[ReceivedMessage, None]:
        """
        Get the original message this one is replied to.

        May fail due to the replied message is flushed out of chat history, or it is a constructed one

        :return: content or None
        """
        pass


class ReceivedMessage:
    """
    Received message
    """

    def __init__(self):
        self._time: datetime.datetime = None
        self._channel: Channel = None
        self._sender: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None
        self._msgID: str = None
        self._msgContent: MessageContent = None
        self._reply: RepliedMessage = None

    def __str__(self):
        return dumps({
            'time': str(self._time),
            'sender': str(self._sender),
            'msgID': self._msgID,
            'msgContent': str(self._msgContent),
            'reply_to': str(self._reply),
        }, ensure_ascii=False)

    def get_channel(self) -> Channel:
        """
        Get the channel this message comes from

        May be the same as get_sender() if it is a private message

        :return: channel obj
        """
        return self._channel

    def get_sender(self) -> Union[Friend, Stranger, GroupMember, GroupAnonymousMember]:
        """
        Get the sender of this message, either a friend or someone from a group

        :return: sender object
        """
        return self._sender

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

    async def quoted_reply(self, content: MessageContent) -> Union[str, None]:
        """
        Reply to original message with its content summarized and quoted

        :param content: message content
        :return: msgID of reply msg or None if failed
        """
        pass


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
        self._revokee: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None

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

    def get_revokee(self) -> User:
        """
        Get the one whose message was revoked

        :return: user object
        """
        return self._revoker

    async def get_remoked_msg(self) -> ReceivedMessage:
        """
        Get the original message which was revoked

        May fail due to the replied message is flushed out of chat history

        :return: message object
        """
        pass
